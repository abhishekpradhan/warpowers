// Exercise the actual frontend through its public API with a CPU-only backend.
#include "d8web/d3d8.h"
#include "core/backend.h"

#include <cstdio>
#include <cstring>
#include <limits>
#include <string>

namespace d8web {
unsigned liveTextures = 0;
class TestBackend final : public IBackend {
public:
    bool init(int, int) override { return true; }
    void resize(int, int) override {}
    BackendHandle createBuffer(BufferKind, UINT, bool) override { return ++next; }
    void updateBuffer(BackendHandle, UINT, const void*, UINT, bool) override {}
    void destroyBuffer(BackendHandle) override {}
    BackendHandle createTexture(UINT, UINT, UINT, TexFormat) override { ++liveTextures; return ++next; }
    void updateTexture(BackendHandle, UINT, UINT, UINT, TexFormat, const void*, UINT) override {}
    void destroyTexture(BackendHandle) override { --liveTextures; }
    void setViewport(const D3DVIEWPORT8&) override {}
    void clear(bool, bool, bool, D3DCOLOR, float, DWORD) override {}
    void draw(const DrawGeometry&, const StateSnapshot&, const ShaderKey&) override {}
    void present() override {}
    const char* name() const override { return "resource-contract"; }
private:
    BackendHandle next = 0;
};
IBackend* createWebGL2Backend() { return new TestBackend; }
}

using namespace d8web;

static int failure(const char* message) {
    std::fprintf(stderr, "FAIL: %s\n", message);
    return 1;
}

static int copyCase(IDirect3DDevice8* device, const std::string& mode) {
    IDirect3DSurface8 *source = nullptr, *destination = nullptr;
    device->CreateImageSurface(4, 4, D3DFMT_A8R8G8B8, &source);
    device->CreateImageSurface(4, 4, D3DFMT_A8R8G8B8, &destination);
    D3DLOCKED_RECT locked{};
    source->LockRect(&locked, nullptr, 0);
    std::memset(locked.pBits, 0x73, 64);
    source->UnlockRect();
    RECT rect{0, 0, 2, 2};
    POINT point{1, 1};
    if (mode == "copy-source-outside") rect = {5, 0, 6, 1};
    if (mode == "copy-source-outside-y") rect = {0, 5, 1, 6};
    if (mode == "copy-source-crosses-edge") rect = {3, 0, 5, 1};
    if (mode == "copy-destination-outside") point = {5, 0};
    if (mode == "copy-destination-outside-y") point = {0, 5};
    if (mode == "copy-destination-crosses-edge") point = {3, 0};
    if (mode == "copy-reversed") rect = {2, 0, 1, 1};
    if (mode == "copy-reversed-height") rect = {0, 2, 1, 1};
    if (mode == "copy-negative") rect = {-1, 0, 1, 1};
    if (mode == "copy-negative-point") point = {-1, 0};
    if (mode == "copy-empty") rect = {0, 0, 0, 1};
    if (mode == "copy-empty-height") rect = {0, 0, 1, 0};
    if (mode == "copy-extreme") rect = {std::numeric_limits<LONG>::min(), 0,
                                      std::numeric_limits<LONG>::max(), 1};
    const RECT multiRects[] = {{0, 0, 1, 1}, {0, 0, 1, 1}};
    const RECT invalidRects[] = {{0, 0, 1, 1}, {5, 0, 6, 1}};
    const POINT multiPoints[] = {{0, 0}, {3, 3}};
    HRESULT result;
    if (mode == "copy-self") {
        result = device->CopyRects(destination, &rect, 1, destination, &point);
    } else if (mode == "copy-full") {
        result = device->CopyRects(source, nullptr, 0, destination, nullptr);
    } else if (mode == "copy-default-point") {
        result = device->CopyRects(source, &rect, 1, destination, nullptr);
    } else if (mode == "copy-multiple" || mode == "copy-invalid-second") {
        result = device->CopyRects(source, mode == "copy-multiple" ? multiRects : invalidRects,
                                   2, destination, multiPoints);
    } else {
        result = device->CopyRects(source, &rect, 1, destination, &point);
    }
    const bool valid = mode == "copy-valid" || mode == "copy-full" ||
                       mode == "copy-default-point" || mode == "copy-multiple";
    if (result != (valid ? D3D_OK : D3DERR_INVALIDCALL))
        return failure("CopyRects returned the wrong result");
    destination->LockRect(&locked, nullptr, 0);
    const auto* bytes = static_cast<const BYTE*>(locked.pBits);
    for (unsigned y = 0; y < 4; ++y) {
        for (unsigned x = 0; x < 4; ++x) {
            bool copied = mode == "copy-valid" && x >= 1 && x < 3 && y >= 1 && y < 3;
            if (mode == "copy-full") copied = true;
            if (mode == "copy-default-point") copied = x < 2 && y < 2;
            if (mode == "copy-multiple") copied = (x == 0 && y == 0) || (x == 3 && y == 3);
            const BYTE expected = copied ? 0x73 : 0;
            for (unsigned channel = 0; channel < 4; ++channel)
                if (bytes[y * locked.Pitch + x * 4 + channel] != expected)
                    return failure("CopyRects changed a pixel outside the accepted rectangle");
        }
    }
    destination->UnlockRect();
    source->Release();
    destination->Release();
    return 0;
}

static int lifetimeCase(IDirect3DDevice8* device, const std::string& mode) {
    IDirect3DTexture8* texture = nullptr;
    IDirect3DSurface8 *first = nullptr, *second = nullptr;
    device->CreateTexture(4, 4, 3, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &texture);
    if (mode == "lifetime-no-surface") {
        texture->Release();
        return liveTextures == 0 ? 0 : failure("texture without level views leaked");
    }
    texture->GetSurfaceLevel(0, &first);
    if (mode == "lifetime-surfaces-first" || mode == "lifetime-reacquire") {
        first->Release();
        if (liveTextures != 1) return failure("level view consumed the caller's texture reference");
        if (mode == "lifetime-surfaces-first") {
            texture->Release();
            return liveTextures == 0 ? 0 : failure("released level view kept texture alive");
        }
        texture->GetSurfaceLevel(0, &first);
    }
    if (mode == "lifetime-two-levels") texture->GetSurfaceLevel(1, &second);
    if (mode == "lifetime-repeated-query") {
        texture->GetSurfaceLevel(0, &second);
    }
    if (mode == "lifetime-extra-ref") first->AddRef();
    if (mode == "lifetime-texture-extra-ref") texture->AddRef();
    texture->Release();
    D3DLOCKED_RECT locked{};
    // The surface reference must keep its parent storage alive after texture release.
    if (first->LockRect(&locked, nullptr, 0) != D3D_OK) return failure("retained surface cannot lock");
    std::memset(locked.pBits, 0x53, 64);
    first->UnlockRect();
    if (liveTextures != 1) return failure("retained surface lost its parent texture");
    first->Release();
    if (mode == "lifetime-extra-ref") first->Release();
    if (second) {
        if (liveTextures != 1) return failure("second level lost its parent texture");
        if (second->LockRect(&locked, nullptr, 0) != D3D_OK) return failure("second level cannot lock");
        if (mode == "lifetime-repeated-query") {
            const auto* bytes = static_cast<const BYTE*>(locked.pBits);
            for (unsigned i = 0; i < 64; ++i)
                if (bytes[i] != 0x53) return failure("level queries did not share pixel storage");
        }
        std::memset(locked.pBits, 0x29, mode == "lifetime-two-levels" ? 16 : 64);
        second->UnlockRect();
        second->Release();
    }
    if (mode == "lifetime-texture-extra-ref") {
        if (liveTextures != 1) return failure("surface consumed the extra texture reference");
        texture->Release();
    }
    return liveTextures == 0 ? 0 : failure("texture leaked after the last surface release");
}

int main(int argc, char** argv) {
    if (argc != 2) return failure("choose a contract case");
    const std::string mode = argv[1];
    IDirect3D8* d3d = CreateDirect3D8();
    IDirect3DDevice8* device = nullptr;
    D3DPRESENT_PARAMETERS parameters{};
    parameters.BackBufferWidth = parameters.BackBufferHeight = 16;
    if (d3d->CreateDevice(0, D3DDEVTYPE_HAL, nullptr, 0, &parameters, &device) != D3D_OK)
        return failure("cannot create test device");
    const int result = mode.starts_with("copy-") ? copyCase(device, mode) : lifetimeCase(device, mode);
    device->Release();
    d3d->Release();
    if (!result) std::printf("PASS %s\n", mode.c_str());
    return result;
}

// War Powers Metal spy — DYLD_INSERT_LIBRARIES interposer.
// Hooks the concrete AGX render-encoder classes (classic + Sampled + Metal4
// "_mtlnext" variants) to log draw calls and bound buffer state at the Metal
// layer. Diagnostic ground truth for the invisible-mesh investigation.
//
// Build: clang -dynamiclib -fobjc-arc -framework Metal -framework Foundation \
//        -arch arm64 -o libwp_metal_spy.dylib wp_metal_spy.m
// Use:   DYLD_INSERT_LIBRARIES must be composed INSIDE the game process env
//        (run.sh's bash strips DYLD_* at exec; launch the binary directly).
//
// NOTE: never touch Metal at dyld-initializer time — the AGX driver's lazy
// internal-shader compile aborts the process. Arm from a delayed dispatch.

#import <Metal/Metal.h>
#import <Foundation/Foundation.h>
#import <objc/runtime.h>
#import <stdio.h>
#import <string.h>

#define WP_LOG(...) do { fprintf(stderr, "[WP_MTL] " __VA_ARGS__); fprintf(stderr, "\n"); fflush(stderr); } while (0)

// ---- generic hook registry: per (class, selector) original IMPs ----
typedef struct { Class cls; SEL sel; IMP orig; } WPHook;
static WPHook g_hooks[160];
static int g_hookCount = 0;

static IMP wp_orig_for(id self, SEL sel) {
  for (Class k = object_getClass(self); k; k = class_getSuperclass(k))
    for (int i = 0; i < g_hookCount; i++)
      if (g_hooks[i].cls == k && sel_isEqual(g_hooks[i].sel, sel))
        return g_hooks[i].orig;
  return NULL;
}

static void wp_hook(Class cls, const char* selName, IMP replacement) {
  SEL sel = sel_registerName(selName);
  Method m = class_getInstanceMethod(cls, sel);
  if (!m) return;                                   // selector family not on this class
  IMP cur = method_getImplementation(m);
  if (cur == replacement) return;                   // inherited from already-hooked ancestor
  if (g_hookCount >= (int)(sizeof(g_hooks)/sizeof(g_hooks[0]))) return;
  // Register under the class that OWNS the Method: shared bases (e.g. the
  // common command-encoder superclass owning endEncoding) serve blit/compute
  // encoders too, and their instances must find the original via their chain.
  Class owner = cls;
  for (Class k = class_getSuperclass(cls); k; k = class_getSuperclass(k)) {
    if (class_getInstanceMethod(k, sel) == m) owner = k;
    else break;
  }
  g_hooks[g_hookCount++] = (WPHook){owner, sel, cur};
  method_setImplementation(m, replacement);
  WP_LOG("hooked -[%s %s] (owner %s) cls=%p orig=%p repl=%p", class_getName(cls), selName,
         class_getName(owner), (__bridge void*)cls, (void*)cur, (void*)replacement);
}

// ---- tracked state (diagnostic; races with multi-encoder use acceptable) ----
#define WP_MAX_VB 31
static __unsafe_unretained id<MTLBuffer> g_vb[WP_MAX_VB];
static NSUInteger g_vbOff[WP_MAX_VB];
static __unsafe_unretained id g_pipeline = nil;
static int g_drawLogBudget = 400;
static int g_histBudget = 80;

static void wp_dump_common(id self, const char* variant, NSUInteger prim,
                           NSUInteger indexCount, NSInteger baseVertex,
                           NSUInteger instanceCount) {
  if (g_histBudget > 0) {
    g_histBudget--;
    WP_LOG("draw%s cls=%s prim=%lu idxCount=%lu baseV=%ld inst=%lu",
           variant, class_getName(object_getClass(self)), (unsigned long)prim,
           (unsigned long)indexCount, (long)baseVertex, (unsigned long)instanceCount);
  }
}

static BOOL wp_want_detail(NSUInteger indexCount) {
  return indexCount == 36 && g_drawLogBudget > 0;
}

static void wp_dump_classic_detail(id self, NSUInteger prim, NSUInteger indexCount,
                                   NSUInteger indexType, id<MTLBuffer> ib, NSUInteger ibOff,
                                   NSInteger baseVertex, NSUInteger instanceCount) {
  g_drawLogBudget--;
  WP_LOG("== 36-index CLASSIC draw cls=%s ==", class_getName(object_getClass(self)));
  WP_LOG("  prim=%lu baseV=%ld inst=%lu pipeline=%p", (unsigned long)prim,
         (long)baseVertex, (unsigned long)instanceCount, (__bridge void*)g_pipeline);
  if (ib) {
    WP_LOG("  ib=%p len=%lu mode=%lu off=%lu type=%s", (__bridge void*)ib,
           (unsigned long)ib.length, (unsigned long)ib.storageMode, (unsigned long)ibOff,
           indexType == MTLIndexTypeUInt16 ? "u16" : "u32");
    if (ib.storageMode == MTLStorageModeShared && ib.contents) {
      const uint16_t* idx = (const uint16_t*)((const char*)ib.contents + ibOff);
      WP_LOG("  idx[0..8]=%u %u %u %u %u %u %u %u %u", idx[0], idx[1], idx[2], idx[3],
             idx[4], idx[5], idx[6], idx[7], idx[8]);
    }
  } else {
    WP_LOG("  ib=NULL!");
  }
  for (int i = 0; i < 4; i++) {
    id<MTLBuffer> vb = g_vb[i];
    if (!vb) continue;
    WP_LOG("  vb[%d]=%p len=%lu mode=%lu off=%lu", i, (__bridge void*)vb,
           (unsigned long)vb.length, (unsigned long)vb.storageMode, (unsigned long)g_vbOff[i]);
    if (vb.storageMode == MTLStorageModeShared && vb.contents) {
      const float* f = (const float*)((const char*)vb.contents + g_vbOff[i]);
      WP_LOG("    f[0..7]= %.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f",
             f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7]);
    }
  }
}

static void wp_dump_mtl4_detail(id self, NSUInteger prim, NSUInteger indexCount,
                                NSUInteger indexType, uint64_t ibAddr, uint64_t ibLen,
                                NSInteger baseVertex, NSUInteger instanceCount) {
  g_drawLogBudget--;
  WP_LOG("== 36-index MTL4 draw cls=%s ==", class_getName(object_getClass(self)));
  WP_LOG("  prim=%lu type=%lu ibAddr=0x%llx ibLen=%llu baseV=%ld inst=%lu pipeline=%p",
         (unsigned long)prim, (unsigned long)indexType, ibAddr, ibLen,
         (long)baseVertex, (unsigned long)instanceCount, (__bridge void*)g_pipeline);
}

// ---- classic draw replacements (indexBuffer is an MTLBuffer object) ----
static void wp_c_draw5(id self, SEL _cmd, NSUInteger prim, NSUInteger n, NSUInteger t,
                       id<MTLBuffer> ib, NSUInteger off) {
  wp_dump_common(self, "C5", prim, n, 0, 1);
  if (wp_want_detail(n)) wp_dump_classic_detail(self, prim, n, t, ib, off, 0, 1);
  ((void (*)(id, SEL, NSUInteger, NSUInteger, NSUInteger, id, NSUInteger))
   wp_orig_for(self, _cmd))(self, _cmd, prim, n, t, ib, off);
}
static void wp_c_draw6(id self, SEL _cmd, NSUInteger prim, NSUInteger n, NSUInteger t,
                       id<MTLBuffer> ib, NSUInteger off, NSUInteger inst) {
  wp_dump_common(self, "C6", prim, n, 0, inst);
  if (wp_want_detail(n)) wp_dump_classic_detail(self, prim, n, t, ib, off, 0, inst);
  ((void (*)(id, SEL, NSUInteger, NSUInteger, NSUInteger, id, NSUInteger, NSUInteger))
   wp_orig_for(self, _cmd))(self, _cmd, prim, n, t, ib, off, inst);
}
static void wp_c_draw8(id self, SEL _cmd, NSUInteger prim, NSUInteger n, NSUInteger t,
                       id<MTLBuffer> ib, NSUInteger off, NSUInteger inst,
                       NSInteger baseV, NSUInteger baseI) {
  wp_dump_common(self, "C8", prim, n, baseV, inst);
  if (wp_want_detail(n)) wp_dump_classic_detail(self, prim, n, t, ib, off, baseV, inst);
  ((void (*)(id, SEL, NSUInteger, NSUInteger, NSUInteger, id, NSUInteger, NSUInteger, NSInteger, NSUInteger))
   wp_orig_for(self, _cmd))(self, _cmd, prim, n, t, ib, off, inst, baseV, baseI);
}

// ---- MTL4 draw replacements (indexBuffer is a raw GPU address) ----
static void wp_m_draw5(id self, SEL _cmd, NSUInteger prim, NSUInteger n, NSUInteger t,
                       uint64_t ibAddr, uint64_t ibLen) {
  wp_dump_common(self, "M5", prim, n, 0, 1);
  if (wp_want_detail(n)) wp_dump_mtl4_detail(self, prim, n, t, ibAddr, ibLen, 0, 1);
  ((void (*)(id, SEL, NSUInteger, NSUInteger, NSUInteger, uint64_t, uint64_t))
   wp_orig_for(self, _cmd))(self, _cmd, prim, n, t, ibAddr, ibLen);
}
static void wp_m_draw6(id self, SEL _cmd, NSUInteger prim, NSUInteger n, NSUInteger t,
                       uint64_t ibAddr, uint64_t ibLen, NSUInteger inst) {
  wp_dump_common(self, "M6", prim, n, 0, inst);
  if (wp_want_detail(n)) wp_dump_mtl4_detail(self, prim, n, t, ibAddr, ibLen, 0, inst);
  ((void (*)(id, SEL, NSUInteger, NSUInteger, NSUInteger, uint64_t, uint64_t, NSUInteger))
   wp_orig_for(self, _cmd))(self, _cmd, prim, n, t, ibAddr, ibLen, inst);
}
static void wp_m_draw8(id self, SEL _cmd, NSUInteger prim, NSUInteger n, NSUInteger t,
                       uint64_t ibAddr, uint64_t ibLen, NSUInteger inst,
                       NSInteger baseV, NSUInteger baseI) {
  wp_dump_common(self, "M8", prim, n, baseV, inst);
  if (wp_want_detail(n)) wp_dump_mtl4_detail(self, prim, n, t, ibAddr, ibLen, baseV, inst);
  ((void (*)(id, SEL, NSUInteger, NSUInteger, NSUInteger, uint64_t, uint64_t, NSUInteger, NSInteger, NSUInteger))
   wp_orig_for(self, _cmd))(self, _cmd, prim, n, t, ibAddr, ibLen, inst, baseV, baseI);
}

// ---- binding/state replacements ----
static void wp_setVB(id self, SEL _cmd, id<MTLBuffer> buffer, NSUInteger offset, NSUInteger index) {
  if (index < WP_MAX_VB) { g_vb[index] = buffer; g_vbOff[index] = offset; }
  ((void (*)(id, SEL, id, NSUInteger, NSUInteger))wp_orig_for(self, _cmd))(self, _cmd, buffer, offset, index);
}
static void wp_setVBOff(id self, SEL _cmd, NSUInteger offset, NSUInteger index) {
  if (index < WP_MAX_VB) g_vbOff[index] = offset;
  ((void (*)(id, SEL, NSUInteger, NSUInteger))wp_orig_for(self, _cmd))(self, _cmd, offset, index);
}
static void wp_setPipe(id self, SEL _cmd, id pipe) {
  g_pipeline = pipe;
  ((void (*)(id, SEL, id))wp_orig_for(self, _cmd))(self, _cmd, pipe);
}

// ---- live-class detection via endEncoding ----
static void wp_endEncoding(id self, SEL _cmd) {
  static Class logged[16];
  static int loggedCount = 0;
  Class c = object_getClass(self);
  BOOL seen = NO;
  for (int i = 0; i < loggedCount; i++) if (logged[i] == c) { seen = YES; break; }
  if (!seen && loggedCount < 16) {
    logged[loggedCount++] = c;
    WP_LOG("LIVE encoder class: %s", class_getName(c));
  }
  IMP orig = wp_orig_for(self, _cmd);
  if (orig) ((void (*)(id, SEL))orig)(self, _cmd);
  else WP_LOG("endEncoding: no orig for %s!", class_getName(c));
}

// ICB execution logger (classic: executeCommandsInBuffer:withRange:)
static void wp_execICB(id self, SEL _cmd, id icb, NSRange range) {
  static int budget = 30;
  if (budget > 0) {
    budget--;
    WP_LOG("executeCommandsInBuffer cls=%s icb=%s range=(%lu,%lu)",
           class_getName(object_getClass(self)), class_getName(object_getClass(icb)),
           (unsigned long)range.location, (unsigned long)range.length);
  }
  ((void (*)(id, SEL, id, NSRange))wp_orig_for(self, _cmd))(self, _cmd, icb, range);
}

// Encoder-factory logger: reveals which command-buffer classes create which
// encoder classes in this process, regardless of where draws go.
static id wp_makeRenc(id self, SEL _cmd, id desc) {
  id enc = ((id (*)(id, SEL, id))wp_orig_for(self, _cmd))(self, _cmd, desc);
  static char logged[24][160];
  static int loggedCount = 0;
  char key[160];
  snprintf(key, sizeof(key), "%s -> %s", object_getClassName(self),
           enc ? object_getClassName(enc) : "(nil)");
  BOOL seen = NO;
  for (int i = 0; i < loggedCount; i++) if (strcmp(logged[i], key) == 0) { seen = YES; break; }
  if (!seen && loggedCount < 24) {
    strlcpy(logged[loggedCount++], key, 160);
    WP_LOG("FACTORY %s", key);
  }
  return enc;
}

// Encoding-string → replacement map. Only exact known ABIs are hooked;
// unknown variants are logged and left alone (a guessed ABI would crash).
typedef struct { const char* enc; IMP imp; } WPShape;
static const WPShape wp_indexed_shapes[] = {
  {"v56@0:8Q16Q24Q32@40Q48",           (IMP)0},  // classic5 — filled in wp_arm
  {"v64@0:8Q16Q24Q32@40Q48Q56",        (IMP)0},  // classic6
  {"v80@0:8Q16Q24Q32@40Q48Q56q64Q72",  (IMP)0},  // classic8
  {"v80@0:8Q16Q24Q32@40Q48Q56Q64Q72",  (IMP)0},  // classic8 (unsigned baseVertex variant)
  {"v56@0:8Q16Q24Q32Q40Q48",           (IMP)0},  // mtl4_5
  {"v64@0:8Q16Q24Q32Q40Q48Q56",        (IMP)0},  // mtl4_6
  {"v80@0:8Q16Q24Q32Q40Q48Q56q64Q72",  (IMP)0},  // mtl4_8
  {"v80@0:8Q16Q24Q32Q40Q48Q56Q64Q72",  (IMP)0},  // mtl4_8 (unsigned baseVertex variant)
};

static void wp_arm(void) {
  IMP shapeImps[] = {(IMP)wp_c_draw5, (IMP)wp_c_draw6, (IMP)wp_c_draw8, (IMP)wp_c_draw8,
                     (IMP)wp_m_draw5, (IMP)wp_m_draw6, (IMP)wp_m_draw8, (IMP)wp_m_draw8};
  int total = objc_getClassList(NULL, 0);
  Class* list = (Class*)malloc(sizeof(Class) * total);
  total = objc_getClassList(list, total);
  for (int i = 0; i < total; i++) {
    Class cls = list[i];
    unsigned mcount = 0;
    Method* ms = class_copyMethodList(cls, &mcount);   // own methods only
    for (unsigned m = 0; m < mcount; m++) {
      const char* selName = sel_getName(method_getName(ms[m]));
      const char* enc = method_getTypeEncoding(ms[m]);
      if (strncmp(selName, "drawIndexedPrimitives:indexCount:", 33) == 0) {
        BOOL matched = NO;
        for (unsigned s = 0; s < sizeof(wp_indexed_shapes)/sizeof(wp_indexed_shapes[0]); s++) {
          if (enc && strcmp(enc, wp_indexed_shapes[s].enc) == 0) {
            wp_hook(cls, selName, shapeImps[s]);
            matched = YES;
            break;
          }
        }
        if (!matched)
          WP_LOG("unhooked draw variant -[%s %s] :: %s", class_getName(cls), selName, enc ? enc : "?");
      } else if (strcmp(selName, "executeCommandsInBuffer:withRange:") == 0 &&
                 enc && strcmp(enc, "v48@0:8@16{_NSRange=QQ}24") == 0) {
        wp_hook(cls, selName, (IMP)wp_execICB);
      } else if (strcmp(selName, "renderCommandEncoderWithDescriptor:") == 0 &&
                 enc && strcmp(enc, "@32@0:8@16") == 0) {
        wp_hook(cls, selName, (IMP)wp_makeRenc);
      }
    }
    free(ms);
  }
  free(list);
  // binding/state/liveness on the known AGX concrete classes
  const char* classNames[] = {
    "AGXG13XFamilyRenderContext",
    "AGXG13XFamilySampledRenderContext",
    "AGXG13XFamilyRenderContext_mtlnext",
    "AGXG13XFamilySampledRenderContext_mtlnext",
  };
  for (unsigned i = 0; i < sizeof(classNames)/sizeof(classNames[0]); i++) {
    Class cls = objc_getClass(classNames[i]);
    if (!cls) continue;
    wp_hook(cls, "setVertexBuffer:offset:atIndex:", (IMP)wp_setVB);
    wp_hook(cls, "setVertexBufferOffset:atIndex:", (IMP)wp_setVBOff);
    wp_hook(cls, "setRenderPipelineState:", (IMP)wp_setPipe);
    wp_hook(cls, "endEncoding", (IMP)wp_endEncoding);
  }
  WP_LOG("armed: %d hooks", g_hookCount);
}

__attribute__((constructor))
static void wp_metal_spy_init(void) {
  WP_LOG("loaded; arming in 10s");
  dispatch_after(dispatch_time(DISPATCH_TIME_NOW, 10 * NSEC_PER_SEC),
                 dispatch_get_global_queue(QOS_CLASS_DEFAULT, 0), ^{ wp_arm(); });
}

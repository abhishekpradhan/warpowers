#!/usr/bin/env python3
"""Serve a staged War Powers build locally with release-equivalent cache rules."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


class GameHandler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.wasm': 'application/wasm', '.js': 'text/javascript'}

    def end_headers(self):
        path = urlsplit(self.path).path
        immutable = path.startswith('/assets/') or any(path.startswith('/' + prefix) for prefix in ('app.', 'core.', 'styles.'))
        self.send_header('Cache-Control', 'public, max-age=31536000, immutable' if immutable else 'no-cache')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()

    def do_GET(self):
        if urlsplit(self.path).path in ('/wp-boot-ok', '/wp-boot-fail'):
            print(self.path, flush=True)
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, fmt, *args):
        if len(args) > 1 and str(args[1]) not in ('200', '304'):
            super().log_message(fmt, *args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parents[1] / 'webstage')
    parser.add_argument('--port', type=int, default=8321)
    parser.add_argument('--host', default='127.0.0.1')
    args = parser.parse_args()
    if not (args.directory / 'build.json').is_file():
        parser.error('No staged build found. Run python3 tools/genwebstage.py first.')
    server = ThreadingHTTPServer((args.host, args.port), partial(GameHandler, directory=str(args.directory)))
    print(f'War Powers ready at http://{args.host}:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()

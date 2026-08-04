#!/usr/bin/env python3
"""
Tiny static server for the Vinyl EQ page. Port is fully configurable.

  python3 serve.py                 # port 8080 (or $VINYL_EQ_PORT)
  python3 serve.py --port 9000     # any port you like
  python3 serve.py --port 9000 --dir /path/to/page --host 0.0.0.0

Env: VINYL_EQ_PORT overrides the default port (handy for systemd).
"""
import argparse, os, http.server, socketserver

ap = argparse.ArgumentParser(description="Serve the Vinyl EQ visualizer.")
ap.add_argument("--port", type=int, default=int(os.environ.get("VINYL_EQ_PORT", "8080")),
                help="TCP port (default 8080 or $VINYL_EQ_PORT)")
ap.add_argument("--dir", default=os.path.dirname(os.path.abspath(__file__)),
                help="directory to serve (default: this script's folder)")
ap.add_argument("--host", default="0.0.0.0", help="bind address (default 0.0.0.0)")
args = ap.parse_args()

os.chdir(args.dir)


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer((args.host, args.port), Handler) as httpd:
    print(f"Vinyl EQ serving {args.dir} on http://{args.host}:{args.port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

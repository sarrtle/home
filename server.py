#!/usr/bin/env python3
"""
Sarrtle — single-page portfolio server.

Serves the site from this project directory using only the Python standard
library (http.server). No frameworks, no dependencies, no build step.

Run:
    python server.py                  # binds 0.0.0.0:8000 (reachable from LAN)
    python server.py --port 9000      # different port
    python server.py --host 127.0.0.1 # localhost only

Behaviour:
  * Serves static files from the project root ("/" -> index.html).
  * Correct MIME types for common web assets, including .svg/.webp/.woff2.
  * Clean, themed error pages: 400 malformed request, 403 forbidden path,
    404 missing file, 405 unsupported method, 500 server error.
  * Directory URLs resolve to their index.html (e.g. "/blog/" -> /blog/index.html).
  * Refuses to serve hidden entries (.git, .agent, ...), underscore-prefixed
    names (_research, __pycache__, ...), and any path that resolves outside
    the project root (defense against traversal and symlinks).
  * Conditional GET support: Last-Modified / If-Modified-Since -> 304.

Requires Python 3.7+ (runs on the project's 3.14 / Termux).
"""

import argparse
import datetime
import html
import http.server
import mimetypes
import os
import posixpath
import socket
import sys
import urllib.parse
from email.utils import format_datetime, parsedate_to_datetime

ROOT = os.path.dirname(os.path.abspath(__file__))

# Extensions mimetypes may not know on every platform.
for _ext, _mime in {
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".md": "text/markdown; charset=utf-8",
    ".map": "application/json",
}.items():
    mimetypes.add_type(_mime, _ext)

# Images/fonts are cached for an hour; the HTML page stays fresh.
# CSS/JS are served no-cache so edits show immediately (debug-friendly);
# images and fonts are effectively immutable in practice, so they get the
# 1h cache as the bandwidth optimization.
CACHEABLE_EXTS = frozenset(
    {".svg", ".txt", ".md", ".json", ".map",
     ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2"}
)

ERROR_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>{code} &mdash; Sarrtle</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; margin: 0; }}
  body {{
    min-height: 100vh; display: grid; place-items: center; padding: 2rem;
    background: #0b0e0d; color: #e9e7e0;
    font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  }}
  .card {{ text-align: center; max-width: 30rem; }}
  .mono {{ font-family: ui-monospace, "Cascadia Code", "JetBrains Mono", Menlo, Consolas, monospace; }}
  .code {{ color: #7fe08b; font-size: .85rem; letter-spacing: .08em; margin-bottom: 1.4rem; }}
  h1 {{ font-size: 2.1rem; font-weight: 700; letter-spacing: -.02em; line-height: 1.15; }}
  h1 span {{ color: #727b76; font-weight: 400; }}
  p {{ color: #a5aca7; margin-top: .9rem; line-height: 1.6; font-size: .95rem; }}
  a {{
    display: inline-block; margin-top: 1.7rem; padding: .6rem 1.3rem;
    background: #7fe08b; color: #0b120d; border-radius: .5rem;
    text-decoration: none; font-weight: 600; font-size: .95rem;
  }}
  a:hover {{ background: #57d071; }}
</style>
</head>
<body>
  <div class="card">
    <div class="mono code">MK &middot; {code}</div>
    <h1>{code} <span>&mdash; {title}</span></h1>
    <p>{message}</p>
    <a href="/">Back to home</a>
  </div>
</body>
</html>"""


class _BadRequest(Exception):
    """Malformed request path."""


class _Forbidden(Exception):
    """Path resolves outside the served root."""


class _NotFound(Exception):
    """Hidden entry or nonexistent resource."""


class SiteHandler(http.server.SimpleHTTPRequestHandler):
    server_version = "sarrtle/0.1"
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("directory", ROOT)
        super().__init__(*args, **kwargs)

    # ------------------------------------------------------------------ #
    # Path resolution (never returns a path outside ROOT)
    # ------------------------------------------------------------------ #
    def _resolve(self):
        path = urllib.parse.urlsplit(self.path).path
        try:
            path = urllib.parse.unquote(path, errors="strict")
        except UnicodeDecodeError:
            raise _BadRequest
        if "\x00" in path or any(ord(c) < 32 for c in path):
            raise _BadRequest
        if path in ("", "/"):
            return os.path.join(ROOT, "index.html")
        parts = posixpath.normpath(path).lstrip("/").split("/")
        if any(not part for part in parts):
            raise _NotFound
        for part in parts:
            if part.startswith((".", "_")):
                # hides .git, .agent, _research, __pycache__, dotfiles ...
                raise _NotFound
            if part == "..":              # traversal (normpath already folds most)
                raise _Forbidden
        full = os.path.join(ROOT, *parts)
        if os.path.isdir(full):
            # Directory URLs resolve to their index.html (404 if absent).
            full = os.path.join(full, "index.html")
        # Belt-and-braces containment check (e.g. symlinks pointing out).
        real = os.path.realpath(full)
        root_real = os.path.realpath(ROOT)
        if real != root_real and not real.startswith(root_real + os.sep):
            raise _Forbidden
        return full

    # ------------------------------------------------------------------ #
    # Serving
    # ------------------------------------------------------------------ #
    def _serve(self, method):
        try:
            full = self._resolve()
        except _BadRequest:
            return self.send_error(400, "Bad Request",
                                   "The request path could not be understood.")
        except _Forbidden:
            return self.send_error(403, "Forbidden",
                                   "That path is outside the served site directory.")
        except _NotFound:
            return self.send_error(404, "Not Found",
                                   "The page or file you requested does not exist.")
        if not os.path.isfile(full):
            return self.send_error(404, "Not Found",
                                   "The page or file you requested does not exist.")
        try:
            with open(full, "rb") as fh:
                st = os.fstat(fh.fileno())
                mtime = datetime.datetime.fromtimestamp(
                    st.st_mtime, datetime.timezone.utc)

                # Conditional GET.
                ims = self.headers.get("If-Modified-Since")
                if ims:
                    try:
                        since = parsedate_to_datetime(ims)
                        if since.tzinfo is None:
                            since = since.replace(tzinfo=datetime.timezone.utc)
                        if mtime.replace(microsecond=0) <= since:
                            self.send_response(304, "Not Modified")
                            self.send_header("Cache-Control", "no-cache")
                            self.end_headers()
                            return
                    except (TypeError, ValueError):
                        pass  # unparseable date: serve normally

                ctype, _encoding = mimetypes.guess_type(full)
                ctype = ctype or "application/octet-stream"
                if ctype.startswith("text/") and "charset=" not in ctype:
                    ctype += "; charset=utf-8"

                self.send_response(200, "OK")
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(st.st_size))
                self.send_header("Last-Modified", format_datetime(mtime, usegmt=True))
                self.send_header("Cache-Control",
                                 "public, max-age=3600"
                                 if os.path.splitext(full)[1].lower() in CACHEABLE_EXTS
                                 else "no-cache")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                if method == "GET":
                    self.copyfile(fh, self.wfile)
        except OSError:
            self.send_error(500, "Internal Server Error",
                            "The server could not read the requested file.")

    def do_GET(self):
        self._serve("GET")

    def do_HEAD(self):
        self._serve("HEAD")

    def _not_allowed(self):
        return self.send_error(
            405, "Method Not Allowed",
            "This server only supports GET and HEAD requests.")

    do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = _not_allowed

    # ------------------------------------------------------------------ #
    # Themed error pages
    # ------------------------------------------------------------------ #
    def send_error(self, code, message=None, explain=None):
        try:
            message = message or self.responses.get(code, ("Error", "Error"))[0]
            explain = explain if explain is not None else \
                self.responses.get(code, ("Error", "Error"))[1]
            body = ERROR_PAGE.format(code=code,
                                     title=html.escape(message),
                                     message=html.escape(explain)).encode("utf-8")
            # A malformed request line leaves request_version at the stdlib
            # default "HTTP/0.9", which makes send_response omit the status
            # line and emit a body-only HTTP/0.9-style reply. Force a real
            # HTTP status line so clients always see a proper response.
            if self.request_version == "HTTP/0.9":
                self.request_version = "HTTP/1.1"
            self.send_response(code, message)
            if code == 405:
                self.send_header("Allow", "GET, HEAD")
            self.send_header("Connection", "close")
            self.close_connection = True
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionError):
            pass  # client went away; nothing useful to do


class PortfolioServer(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def lan_ips():
    """Best-effort list of IPv4 addresses on this machine."""
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ips.add(s.getsockname()[0])
        except OSError:
            pass
        finally:
            s.close()
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    return sorted(ips)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Sarrtle — stdlib-only static portfolio server.")
    parser.add_argument("--host", default="0.0.0.0",
                        help="interface to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000,
                        help="port to listen on (default: 8000)")
    args = parser.parse_args(argv)

    try:
        server = PortfolioServer((args.host, args.port), SiteHandler)
    except OSError as exc:
        if exc.errno in (98, 10048, 10013):  # EADDRINUSE / EACCES variants
            sys.stderr.write(
                f"error: cannot bind {args.host}:{args.port} — {exc.strerror}.\n"
                f"       try a different port, e.g.  python server.py --port 9000\n")
            return 1
        raise

    print("Sarrtle — Mark", flush=True)
    print(f"  local:    http://127.0.0.1:{args.port}/", flush=True)
    if args.host in ("0.0.0.0", "::"):
        for ip in lan_ips():
            if not ip.startswith("127."):
                print(f"  network:  http://{ip}:{args.port}/", flush=True)
    print("  press Ctrl+C to stop", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
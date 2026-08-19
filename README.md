# Sarrtle

Portfolio and client-conversion landing page for Mark, an independent
programmer. A single-page, fully static site — no frameworks, no build step,
no CDN, no trackers.

## Run locally (debug)

```bash
python server.py                # serves on 0.0.0.0:8000 (reachable from LAN)
python server.py --port 9000    # different port
python server.py --host 127.0.0.1   # localhost only
```

Open http://127.0.0.1:8000/ in a browser. Works in Termux with a stock
Python install. Requires Python 3.7+. Press `Ctrl+C` to stop.

The Python server is a zero-dependency stdlib server (standard library only)
for local development: static files, MIME types, caching (304), themed
400/403/404/405/500 pages.

## Host anywhere (static)

The site itself is only four files — no server required:

```text
index.html       all site content (single page)
css/styles.css   design system and layout (no external assets)
js/main.js       tiny vanilla JS: nav state, scrollspy, reveal, year
assets/          favicon.svg
```

Deploy those four files to any static host: **GitHub Pages**, Netlify,
Cloudflare Pages, Vercel, plain nginx/apache. GitHub Pages serves the repo
root, which is exactly the layout `server.py` serves locally — same files,
same paths, so local debug results match production.

Notes for static hosting:
- The host sets its own cache headers (GitHub Pages caches css/js/assets).
  The Python-sided `CACHEABLE_EXTS` (1h max-age) is dev-only convenience.
- No `?v=` cache-busters are used; if an edited css/js ever looks stale on
  the host, hard-refresh (the host caches css/js for up to an hour).
- Error pages: static hosts show their own 404 by default.

## Structure

```text
server.py        stdlib HTTP server (ThreadingHTTPServer) for local dev:
                 static files, MIME types, caching (304), themed 400/403/
                 404/405/500 pages. Refuses hidden paths (.git, .agent,
                 dotfiles) and traversal.
index.html       all site content (single page)
css/styles.css   design system and layout (no external assets)
js/main.js       tiny vanilla JS: nav state, scrollspy, reveal, year
assets/          favicon.svg
```

## Editing content

- **Availability status** — hero status pill in `index.html` (search `status-pill`).
- **Contact email** — contact section in `index.html` (search `mynetwork.gravel372@passinbox.com`).
- **Featured work** — `#work` section; keep every card labeled honestly
  (personal project / experiment / demo).

Content policy: no fabricated claims. No invented clients, testimonials, counts,
years of experience, or metrics. If something isn't known, it's omitted.

## Checks

Quick smoke test:

```bash
python server.py --port 8765 &   # then:
curl -I http://127.0.0.1:8765/                 # 200 text/html
curl -I http://127.0.0.1:8765/css/styles.css    # 200 text/css
curl -I http://127.0.0.1:8765/nope.html         # 404
curl -I http://127.0.0.1:8765/.agent/task.md    # 404 (hidden paths refused)
```
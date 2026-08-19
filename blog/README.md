# Blog — Sarrtle

Static, zero-build blog. Posts are hand-written HTML; `posts.json` is the
single source of truth for listings.

## Layout

- `posts.json` — post catalog (schema below). Drives the homepage latest-3,
  the blog index and the category filter chips.
- `index.html` — blog index. The listing and chips are rendered by
  `../js/blog.js`; a `<noscript>` fallback lives in the page.
- `posts/<slug>/index.html` — each post, self-contained.
- `posts/<slug>/media/` — optimized copies of the post's media (WebP/GIF),
  copied from `_research/` at publish time. Posts never link into
  `_research/` (it is committed to the repo but never published or served);
  provenance is recorded in each entry's `researchSource` field.

## posts.json schema

```json
{
  "posts": [
    {
      "slug": "...",
      "title": "...",
      "date": "2026-08-18",
      "updated": null,
      "author": "Mark",
      "category": "Automation | Data & Analysis | AI | Dev tooling | Meta/Notes",
      "tags": ["..."],
      "excerpt": "1-2 sentences...",
      "cover": "posts/slug/media/cover.webp",
      "coverAlt": "optional short description of the cover image",
      "readingTime": 4,
      "status": "published | draft",
      "researchSource": "_research/topic/..."
    }
  ]
}
```

Field notes:

- `slug` — URL segment, `blog/posts/<slug>/`.
- `date` / `updated` — ISO dates; `updated` is shown when set.
- `category` — exactly one of the five fixed categories; drives the filter
  chips on the blog index.
- `tags` — small list (≤ 5) shown on cards.
- `cover` — optional; ~1200×630 WebP, used on cards and as `og:image`.
- `status` — `"published"` appears on the site; `"draft"` is hidden
  everywhere (listing code filters it out).
- `researchSource` — provenance: which `_research/` material the post was
  written from. Never linked, never published.

## Publishing checklist

Run this for every post before it goes live:

- [ ] every claim traces back to the cited `researchSource`; no invented
      numbers, metrics, clients or credentials
- [ ] code blocks carry language classes (`language-python`, …) and the
      copy button works (highlight.js wraps them automatically)
- [ ] media is optimized WebP (or GIF ≤ ~2MB); no self-hosted video
- [ ] cover ~1200×630 WebP if used; alt text + captions on all media
- [ ] excerpt is 1–2 sentences; tags ≤ 5; `readingTime` accurate
- [ ] no links into `_research/`; no secrets anywhere
- [ ] `<noscript>` fallback lists updated if a new post was published
- [ ] `python3 tools/gen-sitemap.py` run; regenerated `sitemap.xml` committed
- [ ] local smoke test: `/`, `/blog/`, the post, and the copy button
- [ ] commit `blog: add <slug>`, push, verify the GitHub Pages deploy

## SEO

- `robots.txt` (repo root) — allow all + `Sitemap:` line.
- `sitemap.xml` (repo root) — generated from the catalog:
  `python3 tools/gen-sitemap.py` (run on every publish, commit the output).
- Default social card: `assets/og-default.png` (1200×630, brand-matched) —
  used by the homepage and blog index. Posts with a `cover` use their own
  cover as `og:image` instead.
- Every post page's `<head>` must carry: unique `<title>`, meta description,
  `<link rel="canonical">`, og:title/description/url/image (cover or
  `assets/og-default.png`), twitter:card, and JSON-LD `BlogPosting`.
- BASE_URL is assumed `https://sarrtle.github.io/home/` until the
  repo is created — confirm after first push and update the head tags +
  `tools/gen-sitemap.py` in one commit if it differs.

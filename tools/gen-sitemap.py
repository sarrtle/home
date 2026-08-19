#!/usr/bin/env python3
"""Generate sitemap.xml from blog/posts.json (stdlib only, no deps).

Run after publishing or updating posts (part of the publish checklist):

    python3 tools/gen-sitemap.py

Output: sitemap.xml at repo root (committed; served by GitHub Pages).
Only posts with status "published" are listed.
"""
import json
import pathlib
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Repo is planned as `home` (owner decision, 2026-08-18) → project
# Pages URL https://sarrtle.github.io/home/. Confirm at first push;
# if the final URL differs, change BASE and re-run.
BASE = "https://sarrtle.github.io/home"

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", NS)


def url(urlset, loc, lastmod):
    u = ET.SubElement(urlset, f"{{{NS}}}url")
    ET.SubElement(u, f"{{{NS}}}loc").text = loc
    ET.SubElement(u, f"{{{NS}}}lastmod").text = lastmod


def main():
    urlset = ET.Element(f"{{{NS}}}urlset")
    url(urlset, f"{BASE}/", "2026-08-19")
    url(urlset, f"{BASE}/blog/", "2026-08-19")

    catalog_path = ROOT / "blog" / "posts.json"
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        for p in catalog.get("posts", []):
            if p.get("status") != "published":
                continue
            url(urlset, f"{BASE}/blog/posts/{p['slug']}/",
                p.get("updated") or p.get("date") or "2026-08-19")

    tree = ET.ElementTree(urlset)
    ET.indent(tree, space="  ")
    tree.write(ROOT / "sitemap.xml", encoding="utf-8", xml_declaration=True)
    print(f"sitemap.xml written: {len(urlset)} url(s)")


if __name__ == "__main__":
    main()

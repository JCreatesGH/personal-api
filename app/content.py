"""Load portfolio content from disk: profile JSON + markdown blog posts.
Pure functions over a directory, so tests run on a fixture folder.
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from xml.sax.saxutils import escape

# A slug is a safe file stem — no slashes or traversal.
SLUG_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass
class Post:
    slug: str
    title: str
    date: str
    summary: str
    tags: List[str]
    body: str

    def meta(self) -> dict:
        return {"slug": self.slug, "title": self.title, "date": self.date,
                "summary": self.summary, "tags": self.tags}

    def full(self) -> dict:
        return {**self.meta(), "body": self.body}


def _unquote(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Parse simple `key: value` YAML-ish front matter between --- fences."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if not m:
        return {}, text.strip()
    meta: dict = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            key = k.strip()
            if key == "tags":
                meta["tags"] = [_unquote(t) for t in v.strip().strip("[]").split(",") if t.strip()]
            else:
                meta[key] = _unquote(v)
    return meta, m.group(2).strip()


def load_posts(posts_dir: Path) -> List[Post]:
    posts = [_post_from_path(path) for path in sorted(posts_dir.glob("*.md"))]
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts


def _post_from_path(path: Path) -> Post:
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    return Post(
        slug=path.stem,
        title=meta.get("title", path.stem),
        date=meta.get("date", ""),
        summary=meta.get("summary", ""),
        tags=meta.get("tags", []),
        body=body,
    )


def load_post(posts_dir: Path, slug: str) -> Optional[Post]:
    """Load a single post by slug, reading one file. Rejects unsafe slugs
    (path traversal) instead of scanning every post."""
    if not SLUG_RE.match(slug):
        return None
    path = posts_dir / f"{slug}.md"
    if not path.is_file():
        return None
    return _post_from_path(path)


def filter_by_tag(posts: List[Post], tag: str) -> List[Post]:
    t = tag.lower()
    return [p for p in posts if any(x.lower() == t for x in p.tags)]


def all_tags(posts: List[Post]) -> List[dict]:
    """Every tag with its post count, most-used first."""
    counts: dict = {}
    for p in posts:
        for tag in p.tags:
            counts[tag] = counts.get(tag, 0) + 1
    return [{"tag": k, "count": v}
            for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def _rfc822(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 +0000")
    except ValueError:
        return ""


def render_rss(posts: List[Post], profile: dict, base_url: str) -> str:
    """A valid RSS 2.0 feed of the posts (newest first)."""
    base = base_url.rstrip("/")
    title = f"{profile.get('name', 'Personal')} — Blog"
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0"><channel>',
        f"<title>{escape(title)}</title>",
        f"<link>{escape(base)}</link>",
        f"<description>{escape(profile.get('headline', ''))}</description>",
    ]
    for p in posts:
        link = f"{base}/api/posts/{p.slug}"
        pub = _rfc822(p.date)
        parts.append(
            "<item>"
            f"<title>{escape(p.title)}</title>"
            f"<link>{escape(link)}</link>"
            f'<guid isPermaLink="false">{escape(p.slug)}</guid>'
            f"<description>{escape(p.summary)}</description>"
            + (f"<pubDate>{pub}</pubDate>" if pub else "")
            + "".join(f"<category>{escape(t)}</category>" for t in p.tags)
            + "</item>"
        )
    parts.append("</channel></rss>")
    return "".join(parts)


def load_profile(content_dir: Path) -> dict:
    f = content_dir / "profile.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}

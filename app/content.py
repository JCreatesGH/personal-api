"""Load portfolio content from disk: profile JSON + markdown blog posts.
Pure functions over a directory, so tests run on a fixture folder.
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


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


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Parse simple `key: value` YAML-ish front matter between --- fences."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.DOTALL)
    if not m:
        return {}, text.strip()
    meta: dict = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            v = v.strip()
            if k.strip() == "tags":
                meta["tags"] = [t.strip() for t in v.strip("[]").split(",") if t.strip()]
            else:
                meta[k.strip()] = v
    return meta, m.group(2).strip()


def load_posts(posts_dir: Path) -> List[Post]:
    posts: List[Post] = []
    for path in sorted(posts_dir.glob("*.md")):
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        posts.append(Post(
            slug=path.stem,
            title=meta.get("title", path.stem),
            date=meta.get("date", ""),
            summary=meta.get("summary", ""),
            tags=meta.get("tags", []),
            body=body,
        ))
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts


def load_profile(content_dir: Path) -> dict:
    f = content_dir / "profile.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}

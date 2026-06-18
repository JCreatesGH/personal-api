"""Your own personal data API + a portfolio frontend that consumes it."""
from __future__ import annotations
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from .content import (
    load_posts, load_post, load_profile, filter_by_tag, all_tags, render_rss,
)

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"


def create_app(content_dir: Path = CONTENT) -> FastAPI:
    app = FastAPI(title="Personal API", version="1.1.0",
                  description="now-playing, projects, blog posts, and an RSS feed as JSON.")
    posts_dir = content_dir / "posts"

    @app.get("/api/profile")
    def profile():
        return load_profile(content_dir)

    @app.get("/api/now")
    def now():
        # In production wire this to Spotify/Last.fm; here it's served from profile.json.
        data = load_profile(content_dir)
        return data.get("now", {"status": "offline"})

    @app.get("/api/posts")
    def posts(tag: Optional[str] = None):
        items = load_posts(posts_dir)
        if tag:
            items = filter_by_tag(items, tag)
        return [p.meta() for p in items]

    @app.get("/api/tags")
    def tags():
        return all_tags(load_posts(posts_dir))

    @app.get("/api/posts/{slug}")
    def post(slug: str):
        p = load_post(posts_dir, slug)
        if p is None:
            raise HTTPException(404, "post not found")
        return p.full()

    @app.get("/api/projects")
    def projects():
        return load_profile(content_dir).get("projects", [])

    @app.get("/feed.xml")
    def feed(request: Request):
        xml = render_rss(load_posts(posts_dir), load_profile(content_dir),
                         str(request.base_url))
        return Response(content=xml, media_type="application/rss+xml")

    if STATIC.exists():
        @app.get("/")
        def index():
            return FileResponse(STATIC / "index.html")
        app.mount("/static", StaticFiles(directory=STATIC), name="static")

    return app


app = create_app()

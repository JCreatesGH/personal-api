"""Your own personal data API + a portfolio frontend that consumes it."""
from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .content import load_posts, load_profile

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
STATIC = ROOT / "static"


def create_app(content_dir: Path = CONTENT) -> FastAPI:
    app = FastAPI(title="Personal API", version="1.0.0",
                  description="now-playing, projects, and blog posts as JSON.")

    @app.get("/api/profile")
    def profile():
        return load_profile(content_dir)

    @app.get("/api/now")
    def now():
        # In production wire this to Spotify/Last.fm; here it's served from profile.json.
        data = load_profile(content_dir)
        return data.get("now", {"status": "offline"})

    @app.get("/api/posts")
    def posts():
        return [p.meta() for p in load_posts(content_dir / "posts")]

    @app.get("/api/posts/{slug}")
    def post(slug: str):
        for p in load_posts(content_dir / "posts"):
            if p.slug == slug:
                return p.full()
        raise HTTPException(404, "post not found")

    @app.get("/api/projects")
    def projects():
        return load_profile(content_dir).get("projects", [])

    if STATIC.exists():
        @app.get("/")
        def index():
            return FileResponse(STATIC / "index.html")
        app.mount("/static", StaticFiles(directory=STATIC), name="static")

    return app


app = create_app()

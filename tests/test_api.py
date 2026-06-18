import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_profile(client):
    p = client.get("/api/profile").json()
    assert p["name"] == "Josh" and "links" in p


def test_now(client):
    n = client.get("/api/now").json()
    assert n["status"] in ("online", "offline")


def test_posts_list_and_detail(client):
    posts = client.get("/api/posts").json()
    assert len(posts) >= 2
    assert "body" not in posts[0]            # list returns metadata only
    slug = posts[0]["slug"]
    detail = client.get(f"/api/posts/{slug}").json()
    assert detail["slug"] == slug and "body" in detail


def test_post_404(client):
    assert client.get("/api/posts/nope").status_code == 404


def test_projects(client):
    projects = client.get("/api/projects").json()
    assert isinstance(projects, list) and projects[0]["name"]


def test_posts_tag_filter(client):
    all_posts = client.get("/api/posts").json()
    api_posts = client.get("/api/posts?tag=api").json()
    assert 0 < len(api_posts) < len(all_posts)
    assert all("api" in [t.lower() for t in p["tags"]] for p in api_posts)


def test_tags_endpoint(client):
    tags = client.get("/api/tags").json()
    assert any(t["tag"] == "api" and t["count"] >= 1 for t in tags)


def test_rss_feed(client):
    r = client.get("/feed.xml")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/rss+xml")
    assert "<rss" in r.text and "<item>" in r.text


def test_bad_slug_404(client):
    assert client.get("/api/posts/..%2f..%2fprofile").status_code == 404

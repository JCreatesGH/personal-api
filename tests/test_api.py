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

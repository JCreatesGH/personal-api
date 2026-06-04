from pathlib import Path
from app.content import parse_front_matter, load_posts, load_profile

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"


def test_parse_front_matter():
    meta, body = parse_front_matter("---\ntitle: Hi\ntags: [a, b]\n---\nHello body")
    assert meta["title"] == "Hi"
    assert meta["tags"] == ["a", "b"]
    assert body == "Hello body"


def test_parse_without_front_matter():
    meta, body = parse_front_matter("just text")
    assert meta == {} and body == "just text"


def test_load_posts_sorted_desc():
    posts = load_posts(CONTENT / "posts")
    assert len(posts) >= 2
    dates = [p.date for p in posts]
    assert dates == sorted(dates, reverse=True)
    assert all(p.title and p.slug for p in posts)


def test_load_profile():
    profile = load_profile(CONTENT)
    assert profile["name"] == "Josh"
    assert "projects" in profile

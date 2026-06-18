from pathlib import Path
from app.content import (
    parse_front_matter, load_posts, load_post, load_profile,
    filter_by_tag, all_tags, render_rss,
)

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
POSTS = CONTENT / "posts"


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


def test_front_matter_strips_quotes():
    meta, _ = parse_front_matter('---\ntitle: "Quoted Title"\ntags: ["a", b]\n---\nx')
    assert meta["title"] == "Quoted Title"
    assert meta["tags"] == ["a", "b"]


def test_load_post_by_slug():
    slug = load_posts(POSTS)[0].slug
    assert load_post(POSTS, slug).slug == slug
    assert load_post(POSTS, "does-not-exist") is None


def test_load_post_rejects_traversal():
    assert load_post(POSTS, "../profile") is None
    assert load_post(POSTS, "../../etc/passwd") is None


def test_filter_by_tag_case_insensitive():
    posts = load_posts(POSTS)
    api_posts = filter_by_tag(posts, "API")
    assert api_posts and all("api" in [t.lower() for t in p.tags] for p in api_posts)


def test_all_tags_counts():
    tags = {t["tag"]: t["count"] for t in all_tags(load_posts(POSTS))}
    assert tags.get("api", 0) >= 1 and tags.get("typescript", 0) >= 1


def test_render_rss_is_valid_xml():
    import xml.etree.ElementTree as ET
    posts = load_posts(POSTS)
    xml = render_rss(posts, load_profile(CONTENT), "https://me.example/")
    root = ET.fromstring(xml)                       # parses -> well-formed
    assert root.tag == "rss"
    titles = [i.findtext("title") for i in root.iter("item")]
    assert posts[0].title in titles
    # special characters must be escaped, not break the XML
    safe = render_rss([type(posts[0])(slug="s", title="A & B <x>", date="2026-01-02",
                                      summary="<i>", tags=["c&d"], body="")],
                      {}, "https://x/")
    ET.fromstring(safe)

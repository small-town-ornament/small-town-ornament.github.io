from __future__ import annotations

import shutil
import subprocess
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build_site(tmp_path: Path) -> Path:
    output = tmp_path / "public"
    subprocess.run(
        ["hugo", "--destination", str(output)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return output


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def markdown_body(path: Path) -> str:
    text = read(path)
    if text.startswith("---"):
        return text.split("---", 2)[2]
    return text


def frontmatter_value(path: Path, key: str) -> str:
    match = re.search(rf"^{key}:\s*\"([^\"]+)\"", read(path), re.MULTILINE)
    assert match, f"{path.name} is missing {key}"
    return match.group(1)


def word_count(path: Path) -> int:
    return len(re.findall(r"\b[\w'-]+\b", markdown_body(path)))


def post_files() -> list[Path]:
    return sorted(
        post for post in (ROOT / "content" / "posts").glob("*.md") if post.name != "_index.md"
    )


def test_hugo_site_renders_editorial_core(tmp_path: Path) -> None:
    output = build_site(tmp_path)

    index = read(output / "index.html")
    assert "Small-Town Ornament" in index
    assert "Movement &amp; Fit" in index
    assert "City Dispatches" in index
    assert "Getting Dressed" in index
    assert "Farm Girl Files" in index
    assert "Open Season" in index
    assert "Favorites" in index

    assert (output / "segments" / "movement-and-fit" / "index.html").exists()
    assert (output / "segments" / "city-dispatches" / "index.html").exists()
    assert (output / "favorites" / "index.html").exists()
    assert (output / "about" / "index.html").exists()
    assert (output / "index.xml").exists()


def test_sample_content_uses_public_frontmatter_schemas(tmp_path: Path) -> None:
    output = build_site(tmp_path)

    post = read(output / "posts" / "piedmont-park-before-the-heat" / "index.html")
    assert "Piedmont Park Before The Heat" in post
    assert "Movement &amp; Fit" in post
    assert "hero-image" in post
    assert "More from Movement &amp; Fit" in post
    assert "Back to Movement &amp; Fit" in post
    assert "Next" in post or "Previous" in post

    favorite = read(output / "favorites" / "pho-dai-loi-2" / "index.html")
    assert "Pho Dai Loi #2" in favorite
    assert "Restaurants" in favorite
    assert "Essential" in favorite
    assert "4186 Buford Hwy NE" in favorite


def test_launch_posts_are_substantial_and_cover_farm_girl_files() -> None:
    posts = post_files()
    assert len(posts) >= 4
    assert any("Farm Girl Files" in read(post) for post in posts)

    for post in posts:
        assert word_count(post) >= 400, f"{post.name} needs to read like an essay"
        assert word_count(post) <= 900, f"{post.name} should stay blog-length"


def test_posts_use_unique_existing_hero_images() -> None:
    posts = post_files()
    images = [frontmatter_value(post, "image") for post in posts]
    assert len(images) == len(set(images))

    for image in images:
        assert image.startswith("/images/")
        assert image.endswith(".jpg")
        assert (ROOT / "static" / image.removeprefix("/")).exists()


def test_homepage_invites_subscription_and_deeper_discovery(tmp_path: Path) -> None:
    output = build_site(tmp_path)

    index = read(output / "index.html")
    assert "Subscribe" in index
    assert 'href="/index.xml"' in index
    assert "Monthly small-town dispatches" in index
    assert "Farm Girl Files" in index


def test_place_based_content_is_grounded() -> None:
    favorite = ROOT / "content" / "favorites" / "2026-05-14-buford-highway-pho.md"
    assert frontmatter_value(favorite, "title") != "Buford Highway Pho"
    assert frontmatter_value(favorite, "address")
    assert frontmatter_value(favorite, "hours")
    assert frontmatter_value(favorite, "what_to_order")
    assert frontmatter_value(favorite, "pro_tip")

    required_post_fields = {
        "2026-05-13-oakland-cemetery-on-a-tuesday.md": ["location_note"],
        "2026-05-14-piedmont-park-before-the-heat.md": ["route_note", "what_i_wore"],
        "2026-05-15-decatur-jacket.md": ["where_found", "piece_details"],
    }

    for filename, fields in required_post_fields.items():
        post = ROOT / "content" / "posts" / filename
        for field in fields:
            assert frontmatter_value(post, field)


def test_gallery_shortcode_supports_inline_photo_essays() -> None:
    shortcode = ROOT / "layouts" / "shortcodes" / "post-image.html"
    assert shortcode.exists()
    text = read(shortcode)
    assert ".Page.Params.gallery" in text
    assert "<figure" in text
    assert "figcaption" in text


def test_static_assets_are_present_and_self_contained() -> None:
    css_path = ROOT / "assets" / "css" / "ornament.css"
    assert css_path.exists()
    css = css_path.read_text(encoding="utf-8")
    assert "fonts.googleapis.com" not in css
    assert "gradient" not in css.lower()

    for asset in [
        ROOT / "static" / "images" / "editorial-atlanta.jpg",
        ROOT / "static" / "images" / "oakland-cemetery-on-a-tuesday.jpg",
        ROOT / "static" / "images" / "piedmont-park-before-the-heat.jpg",
        ROOT / "static" / "images" / "decatur-jacket.jpg",
        ROOT / "static" / "images" / "screened-porch-to-city-balcony.jpg",
        ROOT / "static" / "images" / "buford-highway-pho.jpg",
        ROOT / "static" / "favicon.ico",
    ]:
        assert asset.exists()

    assert shutil.which("hugo"), "hugo must be installed for local publishing"

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
    assert len(posts) >= 7
    assert sum(1 for post in posts if "Farm Girl Files" in read(post)) >= 3
    assert any("Open Season" in read(post) for post in posts)

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
    assert "Tuesday is when a city tells the truth about itself." in index
    assert "Caroline walking on an Atlanta street in golden-hour film light" in index
    assert 'href="/posts/triathlon-training-started-as-a-dare/">Latest: Triathlon Training Started As A Dare' in index
    assert "Editorial Atlanta street scene" not in index
    assert "Issue board" in index
    assert "Subscribe" in index
    assert 'href="/index.xml"' in index
    assert "Monthly small-town dispatches" in index
    assert "Farm Girl Files" in index
    assert 'property="og:image"' in index
    assert 'name="twitter:card" content="summary_large_image"' in index


def test_about_and_favorites_have_caroline_voice_and_visuals(tmp_path: Path) -> None:
    output = build_site(tmp_path)

    about = read(output / "about" / "index.html")
    assert "Evergreen, Alabama" in about
    assert "Crimson Cabaret" in about
    assert "not a lifestyle brand" in about
    assert "/images/about-caroline.jpg" in about

    favorites = read(output / "favorites" / "index.html")
    assert "not a civic service announcement" in favorites
    assert "earned a place in my actual rotation" in favorites
    assert "where to park" in favorites

    posts_index = read(output / "posts" / "index.html")
    assert "This is the main table" in posts_index
    assert "earn its length" in posts_index


def test_place_based_content_is_grounded() -> None:
    favorites = sorted((ROOT / "content" / "favorites").glob("*.md"))
    assert len(favorites) >= 4

    for favorite in favorites:
        if favorite.name == "_index.md":
            continue
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


def test_real_places_render_maps_and_routes(tmp_path: Path) -> None:
    output = build_site(tmp_path)

    piedmont = read(output / "posts" / "piedmont-park-before-the-heat" / "index.html")
    assert "route-card" in piedmont
    assert "Piedmont&#43;Park&#43;12th&#43;Street&#43;Entrance" in piedmont
    assert "Open route" in piedmont

    oakland = read(output / "posts" / "oakland-cemetery-on-a-tuesday" / "index.html")
    assert "place-map" in oakland
    assert "Historic&#43;Oakland&#43;Cemetery" in oakland
    assert "Margaret Mitchell" in oakland

    favorite = read(output / "favorites" / "pho-dai-loi-2" / "index.html")
    assert "place-map" in favorite
    assert "Pho&#43;Dai&#43;Loi&#43;2" in favorite
    assert "Parking" in favorite
    assert "Price" in favorite

    route_favorite = read(output / "favorites" / "piedmont-park-morning-loop" / "index.html")
    assert "route-card" in route_favorite
    assert "Open route" in route_favorite


def test_gallery_shortcode_supports_inline_photo_essays() -> None:
    shortcode = ROOT / "layouts" / "shortcodes" / "post-image.html"
    assert shortcode.exists()
    text = read(shortcode)
    assert ".Page.Params.gallery" in text
    assert "<figure" in text
    assert "figcaption" in text


def test_posts_render_inline_photo_essays(tmp_path: Path) -> None:
    output = build_site(tmp_path)

    for post in post_files():
        source = read(post)
        assert source.count("src: \"/images/") >= 3, f"{post.name} needs gallery images"
        assert source.count("{{< post-image") >= 3, f"{post.name} needs inline photo placement"

        rendered = read(output / "posts" / frontmatter_value(post, "slug") / "index.html")
        assert rendered.count("post-figure") >= 3


def test_magazine_polish_from_latest_folio_critique(tmp_path: Path) -> None:
    output = build_site(tmp_path)

    css = read(ROOT / "assets" / "css" / "ornament.css")
    assert ".hero-media img" in css
    assert "object-fit: cover" in css
    assert ".article-body blockquote" in css
    assert "body::before" in css
    assert ".footer-nav" in css

    open_season = read(output / "segments" / "open-season" / "index.html")
    assert "Triathlon Training Started As A Dare" in open_season
    assert "The essays that do not behave" in open_season

    post = read(output / "posts" / "triathlon-training-started-as-a-dare" / "index.html")
    assert "No heroic language. No transformation story." in post
    assert "Swimming is the rude one." in post
    assert "blockquote" in post

    favorites = read(output / "favorites" / "index.html")
    assert "Kudzu Antiques" in favorites
    assert "Piedmont Park Morning Loop" in favorites
    assert "Oakland Cemetery Tuesday Walk" in favorites


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
        ROOT / "static" / "images" / "open-season-southern.jpg",
        ROOT / "static" / "images" / "gallery" / "triathlon-bike-detail.jpg",
        ROOT / "static" / "images" / "gallery" / "triathlon-pool-detail.jpg",
        ROOT / "static" / "images" / "buford-highway-pho.jpg",
        ROOT / "static" / "favicon.ico",
    ]:
        assert asset.exists()

    assert shutil.which("hugo"), "hugo must be installed for local publishing"


def test_editorial_images_are_not_cropped_by_fixed_boxes() -> None:
    css = (ROOT / "assets" / "css" / "ornament.css").read_text(encoding="utf-8")

    assert "object-fit: contain" in css
    assert ".hero-media img {\n  height: 100%;" in css
    assert ".hero-media img {\n  height: 100%;\n  max-height: none;\n  object-fit: cover;" in css
    assert ".hero-image {\n  aspect-ratio" not in css
    assert ".post-card .card-image,\n.favorite-card img {\n  aspect-ratio" not in css


def test_future_image_direction_requires_film_grain_and_natural_light() -> None:
    direction = read(ROOT / "docs" / "image-direction.md")

    assert "Kodak Portra 400" in direction
    assert "visible grain" in direction
    assert "Natural or overcast lighting only" in direction
    assert "no studio-perfect light" in direction
    assert "Caroline identity anchors only" in direction
    assert "do not use prior generated blog art" in direction
    assert "do not cut off the top or bottom" in direction

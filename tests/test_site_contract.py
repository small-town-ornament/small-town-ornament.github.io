from __future__ import annotations

import shutil
import subprocess
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

    favorite = read(output / "favorites" / "buford-highway-pho" / "index.html")
    assert "Buford Highway Pho" in favorite
    assert "Restaurants" in favorite
    assert "Essential" in favorite


def test_static_assets_are_present_and_self_contained() -> None:
    css_path = ROOT / "assets" / "css" / "ornament.css"
    assert css_path.exists()
    css = css_path.read_text(encoding="utf-8")
    assert "fonts.googleapis.com" not in css
    assert "gradient" not in css.lower()

    for asset in [
        ROOT / "static" / "images" / "editorial-atlanta.png",
        ROOT / "static" / "images" / "piedmont-park-before-the-heat.png",
        ROOT / "static" / "images" / "buford-highway-pho.png",
        ROOT / "static" / "favicon.ico",
    ]:
        assert asset.exists()

    assert shutil.which("hugo"), "hugo must be installed for local publishing"

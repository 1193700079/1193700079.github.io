"""Check the generated personal pages and preservation of the existing blog."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import subprocess
import sys


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.links = []
        self.ids = []
        self.h1_count = 0
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "h1":
            self.h1_count += 1
        if tag in {"a", "link", "script", "img"}:
            value = attrs.get("href") or attrs.get("src")
            if value:
                self.links.append(value)


def main():
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "_site").resolve()
    source = Path(__file__).resolve().parents[1]
    required = ["index.html", "cv/index.html", "blog/index.html", "assets/profile/profile.css", "assets/profile/profile.js", "assets/css/main.css", "assets/profile/portrait.jpg", "baidusitemap.xml", "sitemap.xml"]
    for name in required:
        assert (output / name).is_file(), f"Missing output: {name}"
    profile = json.loads((source / "_data/profile.json").read_text())
    assert len(profile["projects"]) == 2
    assert len(profile["experience"]) == 4
    assert (output / "blog/index.html").read_bytes() == (source / "blog/index.html").read_bytes(), "Legacy homepage changed during build"
    baidu_sitemap = source / "baidusitemap.xml"
    if baidu_sitemap.is_file():
        assert (output / "baidusitemap.xml").read_bytes() == baidu_sitemap.read_bytes(), "Legacy Baidu sitemap changed during build"
    tracked_html = subprocess.check_output(["git", "ls-files", "-z", "*.html"], cwd=source).decode("utf-8").split("\0")
    source_articles = [source / name for name in tracked_html if name and name not in {"index.html", "cv.html", "blog/index.html"} and not name.startswith(("_includes/", "_layouts/", "_site/"))]
    assert source_articles, "Legacy page inventory unexpectedly empty"
    for article in source_articles:
        rendered = output / article.relative_to(source)
        assert rendered.is_file(), f"Legacy article missing: {article.relative_to(source)}"
        assert rendered.read_bytes() == article.read_bytes(), f"Legacy article changed: {article.relative_to(source)}"
    pages = {}
    for name in ["index.html", "cv/index.html"]:
        path = output / name
        html = path.read_text(encoding="utf-8")
        assert "{{" not in html and "{%" not in html, f"Unrendered Liquid in {name}"
        assert profile["name_en"] in html and profile["name_zh"] in html
        assert "including cached tokens" in html and "含缓存" in html
        assert "Voxora" in html and "Xcoder" in html
        page = Page(path)
        assert page.h1_count == 1, f"Expected one h1 in {name}"
        assert len(page.ids) == len(set(page.ids)), f"Duplicate IDs in {name}"
        pages[name] = page
    for name, page in pages.items():
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            if url.path:
                target = output / unquote(url.path).lstrip("/") if url.path.startswith("/") else (output / name).parent / unquote(url.path)
            else:
                target = output / name
            if target.is_dir():
                target = target / "index.html"
            assert target.is_file(), f"Broken local link in {name}: {link}"
            if url.fragment and target.suffix == ".html":
                target_page = Page(target)
                assert unquote(url.fragment) in target_page.ids, f"Broken anchor in {name}: {link}"
    cv = (output / "cv/index.html").read_text(encoding="utf-8")
    for text in ["MiniMax H3", "Qwen-Image 2.1", "Qwen3.8-27B", "Qoder", "Qwen3.6-35B-A3B", "智慧绿通", "2025.02", "2024.12", "2024.03", "2023.08"]:
        assert text in cv, f"Required resume fact missing: {text}"
    print(f"PASS: bilingual home and CV, assets, local links, model facts, and {len(source_articles)} unchanged legacy posts.")


if __name__ == "__main__":
    main()

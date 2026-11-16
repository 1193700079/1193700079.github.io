"""Check the generated profile, blog content, routes, and local links."""
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import sys
import xml.etree.ElementTree as ET


SITE_HOST = "1193700079.github.io"
BODY_START = "<!-- article-body:start -->"
BODY_END = "<!-- article-body:end -->"
POST_PATHS = {
    "/css-study-01.html",
    "/mysql-linux.html",
    "/fetch-springboot-oss指南.html",
    "/算法接入平台.html",
    "/my-first-article.html",
}
REMOVED_ROUTES = {"about", "friends"}


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.html = path.read_text(encoding="utf-8")
        self.links = []
        self.ids = []
        self.h1_count = 0
        self.feed(self.html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "h1":
            self.h1_count += 1
        if tag in {"a", "area", "link"} and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag in {"script", "img", "iframe", "source", "video", "audio", "track", "input"} and attrs.get("src"):
            self.links.append(attrs["src"])
        if tag == "video" and attrs.get("poster"):
            self.links.append(attrs["poster"])
        if tag == "object" and attrs.get("data"):
            self.links.append(attrs["data"])


def local_target(output, current, link):
    """Resolve local and same-site URLs without making network requests."""
    url = urlsplit(link)
    if url.scheme not in {"", "http", "https"}:
        return None
    if url.netloc and url.hostname != SITE_HOST:
        return None
    if url.scheme and not url.netloc:
        return None
    path = unquote(url.path or ("/" if url.netloc else ""))
    if not path:
        target = current
    elif path.startswith("/"):
        target = output / path.lstrip("/")
    else:
        target = current.parent / path
    target = target.resolve()
    assert target.is_relative_to(output), f"Local link escapes output: {link}"
    if target.is_dir() or path.endswith("/"):
        target = target / "index.html"
    return target, unquote(url.fragment)


def check_removed_target(output, target, origin, link):
    relative = target.relative_to(output)
    first = relative.parts[0] if relative.parts else ""
    assert first not in REMOVED_ROUTES and first not in {f"{name}.html" for name in REMOVED_ROUTES}, (
        f"Removed-page link in {origin}: {link}"
    )


def main():
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "_site").resolve()
    source = Path(__file__).resolve().parents[1]
    required = [
        "index.html", "cv/index.html", "blog/index.html", "404.html", "photos/index.html",
        "archives/index.html", "archives/2021/index.html", "archives/2021/12/index.html",
        "categories/index.html", "tags/index.html", "assets/profile/profile.css",
        "assets/profile/profile.js", "assets/css/main.css", "assets/profile/portrait.jpg",
        "baidusitemap.xml", "sitemap.xml", "search.xml", "atom.xml",
    ]
    for name in required:
        assert (output / name).is_file(), f"Missing output: {name}"
    for root in [source, output]:
        for name in REMOVED_ROUTES:
            for path in [root / name / "index.html", root / f"{name}.html"]:
                assert not path.exists(), f"Removed page still exists: {path}"

    profile = json.loads((source / "_data/profile.json").read_text(encoding="utf-8"))
    assert len(profile["projects"]) == 2
    assert len(profile["experience"]) == 4
    baidu_sitemap = source / "baidusitemap.xml"
    if baidu_sitemap.is_file():
        assert (output / "baidusitemap.xml").read_bytes() == baidu_sitemap.read_bytes(), "Legacy Baidu sitemap changed during build"

    blog_path = source / "_data/blog.json"
    assert blog_path.is_file(), "Missing blog inventory: _data/blog.json"
    blog = json.loads(blog_path.read_text(encoding="utf-8"))
    posts = blog["posts"]
    assert len(posts) == 5, "Expected five preserved blog posts"
    assert {unquote(urlsplit(post["url"]).path) for post in posts} == POST_PATHS, "Original article URLs changed"

    pages = {}

    def page_at(path):
        if path not in pages:
            pages[path] = Page(path)
        return pages[path]

    def required_route(url):
        resolved = local_target(output, output / "index.html", url)
        assert resolved is not None, f"Expected local blog route: {url}"
        path, _ = resolved
        check_removed_target(output, path, "blog inventory", url)
        assert path.is_file(), f"Missing blog route: {url}"
        return path

    for collection, field in [("categories", "category_url"), ("tags", "tag_url")]:
        entries = blog[collection]
        urls = [entry["url"] for entry in entries]
        assert len(urls) == len(set(urls)), f"Duplicate {collection} routes"
        assert set(urls) == {post[field] for post in posts}, f"Incomplete {collection} inventory"
        for entry in entries:
            required_route(entry["url"])
            assert entry["count"] == sum(post[field] == entry["url"] for post in posts), f"Wrong count for {entry['url']}"

    for post in posts:
        path = required_route(post["url"])
        page = page_at(path)
        html = page.html
        assert html.count(BODY_START) == html.count(BODY_END) == 1, f"Missing or duplicate article markers: {post['url']}"
        start = html.index(BODY_START) + len(BODY_START)
        end = html.index(BODY_END)
        assert end >= start, f"Article markers out of order: {post['url']}"
        body = html[start:end].strip()
        assert sha256(body.encode("utf-8")).hexdigest() == post["body_sha256"], f"Article body changed: {post['url']}"
        assert post["title"] in html, f"Article title missing: {post['url']}"
        for heading in post["toc"]:
            assert heading["id"] in page.ids, f"Article anchor missing: {post['url']}#{heading['id']}"

    for name in ["index.html", "cv/index.html"]:
        page = page_at(output / name)
        html = page.html
        assert "{{" not in html and "{%" not in html, f"Unrendered Liquid in {name}"
        assert profile["name_en"] in html and profile["name_zh"] in html
        assert "including cached tokens" in html and "含缓存" in html
        assert "Voxora" in html and "Xcoder" in html
        assert page.h1_count == 1, f"Expected one h1 in {name}"

    for path in sorted(output.rglob("*.html")):
        name = path.relative_to(output)
        page = page_at(path)
        assert len(page.ids) == len(set(page.ids)), f"Duplicate IDs in {name}"
        for link in page.links:
            resolved = local_target(output, path, link)
            if resolved is None:
                continue
            target, fragment = resolved
            check_removed_target(output, target, name, link)
            assert target.is_file(), f"Broken local link in {name}: {link}"
            if fragment and target.suffix == ".html":
                assert fragment in page_at(target).ids, f"Broken anchor in {name}: {link}"

    for sitemap in sorted(output.rglob("*sitemap*.xml")):
        for element in ET.parse(sitemap).iter():
            if element.tag.rsplit("}", 1)[-1] != "loc":
                continue
            link = (element.text or "").strip()
            if not link:
                continue
            resolved = local_target(output, sitemap, link)
            if resolved is not None:
                target, _ = resolved
                check_removed_target(output, target, sitemap.relative_to(output), link)
                assert target.is_file(), f"Broken sitemap URL in {sitemap.name}: {link}"

    cv = page_at(output / "cv/index.html").html
    for text in ["MiniMax H3", "Qwen-Image 2.1", "Qwen3.8-27B", "Qoder", "Qwen3.6-35B-A3B", "智慧绿通", "2025.02", "2024.12", "2024.03", "2023.08"]:
        assert text in cv, f"Required resume fact missing: {text}"
    print(f"PASS: home/CV facts, 5 article hashes, taxonomy routes, {len(pages)} pages with valid local links, and removed pages absent.")


if __name__ == "__main__":
    main()

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
    "/rl-diffusion-survey.html",
    "/leapquant.html",
    "/qwen-sft-6x.html",
}
REMOVED_ROUTES = {"about", "friends"}


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.html = path.read_text(encoding="utf-8")
        self.links = []
        self.ids = []
        self.h1_count = 0
        self.post_links = []
        self._elements = []
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
        if tag == "a" and attrs.get("href"):
            in_row = any("post-row" in classes for _, classes in self._elements)
            in_heading = any(name == "h2" for name, _ in self._elements)
            if in_row and in_heading:
                self.post_links.append(attrs["href"])
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self._elements.append((tag, attrs.get("class", "").split()))

    def handle_endtag(self, tag):
        for index in range(len(self._elements) - 1, -1, -1):
            if self._elements[index][0] == tag:
                del self._elements[index:]
                break


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
        "archives/index.html", "archives/2026/index.html", "archives/2026/11/index.html",
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
    post_paths = [unquote(urlsplit(post["url"]).path) for post in posts]
    assert len(post_paths) == len(set(post_paths)), "Duplicate article URLs"
    assert POST_PATHS <= set(post_paths), "Original article URLs missing"
    for post, path in zip(posts, post_paths):
        assert post["month"] == post["date"][:7] and post["year"] == post["month"][:4], f"Article archive date mismatch: {post['url']}"
        if path in POST_PATHS:
            assert post["month"] == "2026-11", f"Article archive changed: {post['url']}"
        tags = post["tags"]
        assert isinstance(tags, list) and tags and all(isinstance(tag, str) for tag in tags), f"Invalid article tags: {post['url']}"
        assert len(tags) == len(set(tags)), f"Duplicate article tags: {post['url']}"
        assert post["tag"] == tags[0], f"Primary article tag mismatch: {post['url']}"

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

    post_files = {post["url"]: required_route(post["url"]) for post in posts}
    assert len(set(post_files.values())) == len(posts), "Duplicate article destinations"

    def check_listing(url, members):
        path = required_route(url)
        actual = []
        for link in page_at(path).post_links:
            resolved = local_target(output, path, link)
            assert resolved is not None, f"External article link in {url}: {link}"
            actual.append(resolved[0])
        assert len(actual) == len(set(actual)), f"Duplicate article rows in {url}"
        expected = {post_files[post["url"]] for post in members}
        missing = sorted(str(path.relative_to(output)) for path in expected - set(actual))
        extra = sorted(str(path.relative_to(output)) for path in set(actual) - expected)
        assert set(actual) == expected, f"Wrong article list in {url}: missing={missing}, extra={extra}"

    for collection, field in [("categories", "category"), ("tags", "tag")]:
        entries = blog[collection]
        names = [entry["name"] for entry in entries]
        routes = [required_route(entry["url"]) for entry in entries]
        assert len(names) == len(set(names)), f"Duplicate {collection} names"
        assert len(routes) == len(set(routes)), f"Duplicate {collection} routes"
        expected_names = {post["category"] for post in posts} if collection == "categories" else {tag for post in posts for tag in post["tags"]}
        assert set(names) == expected_names, f"Incomplete {collection} inventory"
        by_name = dict(zip(names, routes))
        for post in posts:
            assert required_route(post[f"{field}_url"]) == by_name[post[field]], f"Wrong {field} URL for {post['url']}"
        for entry in entries:
            members = [post for post in posts if post["category"] == entry["name"]] if collection == "categories" else [post for post in posts if entry["name"] in post["tags"]]
            assert entry["count"] == len(members), f"Wrong count for {entry['url']}"
            check_listing(entry["url"], members)

    check_listing("/blog/", posts)
    check_listing("/archives/", posts)
    for year in sorted({post["year"] for post in posts}):
        check_listing(f"/archives/{year}/", [post for post in posts if post["year"] == year])
    for month in sorted({post["month"] for post in posts}):
        check_listing(f"/archives/{month.replace('-', '/')}/", [post for post in posts if post["month"] == month])

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
    print(f"PASS: home/CV facts, {len(posts)} article hashes, taxonomy/archive listings, {len(pages)} pages with valid local links, and removed pages absent.")


if __name__ == "__main__":
    main()

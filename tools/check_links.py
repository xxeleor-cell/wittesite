"""Проверка ссылок и ресурсов сайта на запущенном сервере.

Запуск: python3 tools/check_links.py [http://localhost:8080]
Обходит все HTML-страницы, начиная с главной, и проверяет каждую ссылку href/src.
"""
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urldefrag, urljoin, urlparse

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
cache = {}


def fetch(url):
    if url in cache:
        return cache[url]
    is_page = url.endswith("/")
    req = urllib.request.Request(url, method="GET" if is_page else "HEAD")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            cache[url] = (r.status, r.read().decode("utf-8", "ignore") if is_page else "")
    except urllib.error.HTTPError as e:
        cache[url] = (e.code, "")
    return cache[url]


def main():
    queue, visited, errors, pages = ["/"], {"/"}, [], 0
    host = urlparse(BASE).netloc
    while queue:
        path = queue.pop()
        code, body = fetch(urljoin(BASE, path))
        if code != 200:
            errors.append(("—", path, code))
            continue
        pages += 1
        for link in re.findall(r'(?:href|src)="([^"]+)"', body):
            link = urldefrag(link)[0]
            if not link or link.startswith(("mailto:", "tel:", "#")):
                continue
            full = urljoin(urljoin(BASE, path), link)
            if urlparse(full).netloc != host:
                continue
            c, _ = fetch(full)
            if c != 200:
                errors.append((path, link, c))
            p = urlparse(full).path
            if full.endswith("/") and p not in visited:
                visited.add(p)
                queue.append(p)
    print(f"HTML-страниц: {pages}, проверено адресов: {len(cache)}")
    for e in errors:
        print("ОШИБКА:", e)
    print(f"Ошибок: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

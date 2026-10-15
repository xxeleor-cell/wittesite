"""Локальный сервер сайта Witte-rus.

Запуск:  python3 tools/server.py [порт]        (по умолчанию 8080)
Открыть: http://localhost:8080/

Отдаёт статические файлы из site/ и принимает заявки формы «Запросить КП»
(POST /api/request). Заявки сохраняются построчно в data/requests/requests.jsonl.
"""
import datetime
import http.server
import json
import os
import socketserver
import sys
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
REQ_DIR = os.path.join(ROOT, "data", "requests")
FIELDS = ["name", "company", "phone", "email", "region", "direction", "products", "comment", "page"]


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=SITE, **kw)

    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml",
                      ".xml": "application/xml; charset=utf-8", ".txt": "text/plain; charset=utf-8",
                      ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
                      ".js": "text/javascript; charset=utf-8"}

    def send_error(self, code, message=None, explain=None):
        if code == 404 and self.command == "GET":
            path = os.path.join(SITE, "404.html")
            if os.path.exists(path):
                body = open(path, "rb").read()
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        super().send_error(code, message, explain)

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/request":
            return self._json(404, {"error": "Не найдено"})
        try:
            length = min(int(self.headers.get("Content-Length", 0)), 64 * 1024)
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return self._json(400, {"error": "Некорректные данные"})
        if data.get("website"):  # поле-ловушка для ботов
            return self._json(200, {"id": "0"})
        rec = {k: str(data.get(k, ""))[:2000].strip() for k in FIELDS}
        digits = "".join(ch for ch in rec["phone"] if ch.isdigit())
        if not rec["name"] or len(digits) < 10 or not data.get("consent"):
            return self._json(422, {"error": "Заполните имя, телефон и подтвердите согласие."})
        rec["id"] = datetime.datetime.now().strftime("%y%m%d") + "-" + uuid.uuid4().hex[:5].upper()
        rec["created"] = datetime.datetime.now().isoformat(timespec="seconds")
        os.makedirs(REQ_DIR, exist_ok=True)
        with open(os.path.join(REQ_DIR, "requests.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"Новая заявка {rec['id']}: {rec['name']}, {rec['phone']}, {rec['products']}")
        return self._json(200, {"id": rec["id"]})


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    with Server(("0.0.0.0", port), Handler) as httpd:
        print(f"Сайт Witte-rus: http://localhost:{port}/  (Ctrl+C — остановить)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

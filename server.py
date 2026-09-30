#!/usr/bin/env python3
"""Retro-Runners site server — Python standard library only (no pip install needed).

Local:   python3 server.py                 -> http://127.0.0.1:8000
Online:  Render sets PORT automatically; set RR_PIN (admin PIN) and, with a disk, RR_DATA_DIR=/var/data
"""
import hmac, json, mimetypes, os, secrets, shutil, sys, time, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
BASE = Path(os.environ.get("RR_DATA_DIR") or ROOT)      # where edits + uploads are stored
UP, DATA = BASE / "uploads", BASE / "data" / "site.json"
ONLINE = "PORT" in os.environ                            # Render / most hosts set PORT
PIN = os.environ.get("RR_PIN", "amigo")
HOST = os.environ.get("RR_HOST", "0.0.0.0" if ONLINE else "127.0.0.1")
PORT = int(os.environ.get("PORT") or os.environ.get("RR_PORT") or 8000)
KEYS = {"v", "site", "theme", "sections", "projects", "services", "skills", "styles", "crew", "stats"}
TOKENS, FAILS = set(), {}
CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' "
       "https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data: blob:")

def sniff(b):
    if b.startswith(b"\xff\xd8\xff"): return "jpg"
    if b.startswith(b"\x89PNG\r\n\x1a\n"): return "png"
    if b.startswith(b"GIF8"): return "gif"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP": return "webp"

def seed():
    """Create folders; on a fresh disk copy the content committed in Git (data/site.json, uploads/)."""
    UP.mkdir(parents=True, exist_ok=True); DATA.parent.mkdir(parents=True, exist_ok=True)
    if BASE != ROOT:
        src = ROOT / "data" / "site.json"
        if not DATA.exists() and src.exists(): shutil.copy(src, DATA)
        for f in (ROOT / "uploads").glob("*"):
            if f.is_file() and f.name != ".gitkeep" and not (UP / f.name).exists(): shutil.copy(f, UP / f.name)

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def out(self, code, body=b"", ct="application/json", cache="no-cache"):
        if isinstance(body, (dict, list)): body = json.dumps(body).encode()
        if isinstance(body, str): body = body.encode()
        self.send_response(code)
        for k, v in (("Content-Type", ct), ("Content-Length", str(len(body))), ("X-Content-Type-Options", "nosniff"),
                     ("Referrer-Policy", "same-origin"), ("Content-Security-Policy", CSP), ("Cache-Control", cache)):
            self.send_header(k, v)
        self.end_headers(); self.wfile.write(body)

    def body(self, limit):
        n = int(self.headers.get("Content-Length") or 0)
        return None if n > limit else self.rfile.read(n)

    def ip(self): return (self.headers.get("X-Forwarded-For") or self.client_address[0]).split(",")[0].strip()
    def authed(self):
        t = self.headers.get("X-Token", ""); return any(hmac.compare_digest(t, x) for x in TOKENS)

    def do_HEAD(self):
        self.send_response(200); self.end_headers()

    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        if p == "/healthz": return self.out(200, "ok", "text/plain")
        if p == "/api/data":
            try: return self.out(200, json.loads(DATA.read_text("utf-8")))
            except Exception: return self.out(200, {})
        if p == "/": p = "/static/index.html"
        for pre, base, cache in (("/static/", STATIC, "no-cache"), ("/uploads/", UP, "public, max-age=86400")):
            if p.startswith(pre):
                f = (base / urllib.parse.unquote(p[len(pre):])).resolve()
                if base.resolve() in f.parents and f.is_file():
                    return self.out(200, f.read_bytes(), mimetypes.guess_type(f.name)[0] or "application/octet-stream", cache)
        self.out(404, {"error": "not found"})

    def do_POST(self):
        p = urllib.parse.urlparse(self.path).path
        if p == "/api/login":
            ip, now = self.ip(), time.time()
            FAILS[ip] = [t for t in FAILS.get(ip, []) if now - t < 300]
            if len(FAILS[ip]) >= 5: return self.out(429, {"error": "too many tries — wait 5 minutes"})
            try: pin = str(json.loads(self.body(1024)).get("pin", ""))
            except Exception: pin = ""
            if hmac.compare_digest(pin.encode(), PIN.encode()):
                FAILS.pop(ip, None); t = secrets.token_hex(16); TOKENS.add(t); return self.out(200, {"token": t})
            FAILS[ip].append(now); time.sleep(1); return self.out(401, {"error": "bad pin"})
        if not self.authed(): return self.out(401, {"error": "locked"})
        if p == "/api/save":
            b = self.body(1_000_000)
            try: d = json.loads(b)
            except Exception: d = None
            if not isinstance(d, dict): return self.out(400, {"error": "bad json"})
            tmp = DATA.with_suffix(".tmp")
            tmp.write_text(json.dumps({k: d[k] for k in KEYS if k in d}), "utf-8"); tmp.replace(DATA)
            return self.out(200, {"ok": True})
        if p == "/api/upload":
            b = self.body(6_000_000); ext = sniff(b) if b else None
            if not ext: return self.out(400, {"error": "not an image"})
            name = secrets.token_hex(8) + "." + ext
            (UP / name).write_bytes(b); return self.out(200, {"url": "/uploads/" + name})
        self.out(404, {"error": "not found"})

if __name__ == "__main__":
    if ONLINE and PIN == "1985":
        sys.exit("STOP: set a private admin PIN before going online, e.g. RR_PIN=your-secret (Render: Environment tab).")
    seed()
    print(f"Retro-Runners running on {HOST}:{PORT}" + ("" if ONLINE else f"  →  http://127.0.0.1:{PORT}   (admin PIN {'set' if PIN != '1985' else '1985 — change with RR_PIN'})"))
    ThreadingHTTPServer((HOST, PORT), H).serve_forever()

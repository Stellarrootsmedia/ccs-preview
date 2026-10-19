"""Local preview of docs/ that mimics GitHub Pages: /foo serves foo.html, unknown paths get 404.html."""
import http.server, os, sys, pathlib
ROOT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path(__file__).resolve().parent.parent / "docs"
PORT = int(os.environ.get("PORT") or (sys.argv[1] if len(sys.argv) > 1 else 8094))

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=str(ROOT), **k)
    def send_head(self):
        path = self.path.split("?")[0].split("#")[0]
        fs = ROOT / path.lstrip("/")
        if not fs.exists() and (ROOT / (path.strip("/") + ".html")).exists():
            self.path = "/" + path.strip("/") + ".html"
        elif not fs.exists():
            self.send_response(404); self.send_header("Content-Type", "text/html"); self.end_headers()
            self.wfile.write((ROOT / "404.html").read_bytes()); return None
        return super().send_head()
    def end_headers(self):
        self.send_header("Cache-Control", "no-store"); super().end_headers()

http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()

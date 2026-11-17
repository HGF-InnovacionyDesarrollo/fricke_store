r"""Lanzador del portal. Con certificado configurado sirve HTTPS (TLS 1.2+) y redirige HTTP a HTTPS.

  python backend/servidor.py                     # HTTP en 8090 (desarrollo)
  set ECO_TLS_CERT=C:\certs\fricke.pem & set ECO_TLS_KEY=C:\certs\fricke.key & python backend/servidor.py
"""
import os
import ssl
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.dirname(__file__))
import uvicorn  # noqa: E402

import config as cfg  # noqa: E402

PUERTO_HTTP = int(os.environ.get("ECO_PUERTO_HTTP", 8090))
PUERTO_HTTPS = int(os.environ.get("ECO_PUERTO_HTTPS", 8443))
HOST = os.environ.get("ECO_HOST", "0.0.0.0")


class Redireccion(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        host = (self.headers.get("Host") or "").split(":")[0]
        self.send_response(301)
        self.send_header("Location", f"https://{host}:{PUERTO_HTTPS}{self.path}")
        self.end_headers()

    do_POST = do_HEAD = do_GET

    def log_message(self, *a):
        pass


def main():
    if cfg.TLS_CERT and cfg.TLS_KEY:
        threading.Thread(target=HTTPServer((HOST, PUERTO_HTTP), Redireccion).serve_forever, daemon=True).start()
        print(f"{cfg.NOMBRE_PRODUCTO} en https://{HOST}:{PUERTO_HTTPS} (HTTP {PUERTO_HTTP} redirige a HTTPS)")
        uvicorn.run("app:app", app_dir=os.path.dirname(__file__), host=HOST, port=PUERTO_HTTPS,
                    ssl_certfile=cfg.TLS_CERT, ssl_keyfile=cfg.TLS_KEY,
                    ssl_ciphers="ECDHE+AESGCM:ECDHE+CHACHA20", ssl_version=ssl.PROTOCOL_TLS_SERVER,
                    proxy_headers=True)
    else:
        print(f"{cfg.NOMBRE_PRODUCTO} en http://{HOST}:{PUERTO_HTTP} — SIN HTTPS: solo para desarrollo. "
              "Configura ECO_TLS_CERT y ECO_TLS_KEY para producción.")
        uvicorn.run("app:app", app_dir=os.path.dirname(__file__), host=HOST, port=PUERTO_HTTP, proxy_headers=True)


if __name__ == "__main__":
    main()

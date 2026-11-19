r"""Lanzador del portal. Con certificado configurado sirve HTTPS (TLS 1.2+) y redirige HTTP a HTTPS.

  python backend/servidor.py                     # HTTP en 8090 (desarrollo)
  set ECO_TLS_CERT=C:\certs\fricke.pem & set ECO_TLS_KEY=C:\certs\fricke.key & python backend/servidor.py
"""
import os
import ssl
import sys

sys.path.insert(0, os.path.dirname(__file__))
import uvicorn  # noqa: E402

import config as cfg  # noqa: E402

PUERTO_HTTP = int(os.environ.get("ECO_PUERTO_HTTP", 8090))
PUERTO_HTTPS = int(os.environ.get("ECO_PUERTO_HTTPS", 8443))
HOST = os.environ.get("ECO_HOST", "0.0.0.0")


def main():
    if cfg.TLS_CERT and cfg.TLS_KEY:
        import asyncio

        from app import app
        from puerta_equipos import puerta_equipos
        print(f"{cfg.NOMBRE_PRODUCTO} en https://{HOST}:{PUERTO_HTTPS}. El HTTP {PUERTO_HTTP} redirige a HTTPS y solo "
              "acepta los envíos de los equipos (puerta para equipos, ver docs/OPERACION.md).")
        https = uvicorn.Server(uvicorn.Config(app, host=HOST, port=PUERTO_HTTPS,
                                              ssl_certfile=cfg.TLS_CERT, ssl_keyfile=cfg.TLS_KEY,
                                              ssl_ciphers="ECDHE+AESGCM:ECDHE+CHACHA20",
                                              ssl_version=ssl.PROTOCOL_TLS_SERVER, proxy_headers=True))
        http = uvicorn.Server(uvicorn.Config(puerta_equipos(app, PUERTO_HTTPS), host=HOST, port=PUERTO_HTTP,
                                             lifespan="off"))

        async def ambos():
            await asyncio.gather(https.serve(), http.serve())
        asyncio.run(ambos())
    else:
        print(f"{cfg.NOMBRE_PRODUCTO} en http://{HOST}:{PUERTO_HTTP} — SIN HTTPS: solo para desarrollo. "
              "Configura ECO_TLS_CERT y ECO_TLS_KEY para producción.")
        uvicorn.run("app:app", app_dir=os.path.dirname(__file__), host=HOST, port=PUERTO_HTTP, proxy_headers=True)


if __name__ == "__main__":
    main()

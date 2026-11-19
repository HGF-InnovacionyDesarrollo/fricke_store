"""Puerta HTTP solo para equipos (decisión del 19 nov 2026).

Con HTTPS activo, el portal se usa por HTTPS. Los aparatos que aún no hablan HTTPS (los Monitor T/H) siguen enviando
por HTTP a /api/m/<clave>/equipo: esta puerta deja pasar SOLO esas rutas (y solo POST) y redirige todo lo demás a
HTTPS. Si se define ECO_EQUIPOS_REDES (p. ej. "10.20.30.0/24,10.20.31.0/24"), además acepta solo envíos que vengan de
esas redes. La red de los equipos debe estar separada (VLAN) de la de los usuarios: por HTTP la credencial no va cifrada.
"""
import ipaddress
import os
import re

RUTA_EQUIPO = re.compile(r"^/api/m/[a-z0-9_]+/equipo/?$")


def _redes(texto: str) -> list:
    redes = []
    for parte in (texto or "").split(","):
        if parte.strip():
            redes.append(ipaddress.ip_network(parte.strip(), strict=False))
    return redes


def puerta_equipos(app, puerto_https: int, redes: str | None = None):
    """Envuelve la aplicación ASGI para el puerto HTTP."""
    permitidas = _redes(os.environ.get("ECO_EQUIPOS_REDES", "") if redes is None else redes)

    def _ip_permitida(scope) -> bool:
        if not permitidas:
            return True
        try:
            ip = ipaddress.ip_address((scope.get("client") or ("",))[0])
        except ValueError:
            return False
        return any(ip in r for r in permitidas)

    async def _responder(send, estado: int, cabeceras: list, cuerpo: bytes = b""):
        await send({"type": "http.response.start", "status": estado, "headers": cabeceras})
        await send({"type": "http.response.body", "body": cuerpo})

    async def asgi(scope, receive, send):
        if scope["type"] != "http":
            if scope["type"] == "lifespan":
                return await app(scope, receive, send)
            return
        ruta = scope.get("path", "")
        if RUTA_EQUIPO.match(ruta) and scope.get("method") == "POST":
            if not _ip_permitida(scope):
                return await _responder(send, 403, [(b"content-type", b"application/json")],
                                        b'{"detail":"Esta red no puede enviar datos de equipos."}')
            return await app(scope, receive, send)
        host = dict(scope.get("headers") or []).get(b"host", b"").decode("latin-1").split(":")[0] or "localhost"
        destino = f"https://{host}:{puerto_https}{ruta}"
        if scope.get("query_string"):
            destino += "?" + scope["query_string"].decode("latin-1")
        await _responder(send, 301, [(b"location", destino.encode("latin-1")), (b"content-length", b"0")])
    return asgi

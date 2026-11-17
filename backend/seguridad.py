"""RUT, contraseñas y tokens. Solo biblioteca estándar."""
import hashlib
import hmac
import re
import secrets
from pathlib import Path


# ---------------------------------------------------------------- RUT
def _dv(cuerpo: str) -> str:
    suma, factor = 0, 2
    for d in reversed(cuerpo):
        suma += int(d) * factor
        factor = 2 if factor == 7 else factor + 1
    r = 11 - (suma % 11)
    return "0" if r == 11 else "K" if r == 10 else str(r)


def normalizar_rut(texto: str) -> str | None:
    """'12.345.678-5' -> '12345678-5'. Devuelve None si el RUT no es válido."""
    if not texto:
        return None
    limpio = re.sub(r"[^0-9kK]", "", texto).upper()
    if len(limpio) < 2:
        return None
    cuerpo, dv = limpio[:-1], limpio[-1]
    if not cuerpo.isdigit() or not (1_000_000 <= int(cuerpo) <= 99_999_999):
        return None
    if _dv(cuerpo) != dv:
        return None
    return f"{int(cuerpo)}-{dv}"


def formatear_rut(rut: str) -> str:
    cuerpo, dv = rut.split("-")
    return f"{int(cuerpo):,}".replace(",", ".") + "-" + dv


def enmascarar_rut(rut: str) -> str:
    """Para registros donde no hace falta el RUT completo (minimización): 12.***.**8-5"""
    cuerpo, dv = rut.split("-")
    return f"{cuerpo[:2]}.***.**{cuerpo[-1]}-{dv}"


# ---------------------------------------------------------------- contraseñas
# scrypt (memoria-duro) con sal individual. Formato: scrypt$n$r$p$sal_hex$hash_hex
_N, _R, _P = 2**14, 8, 1


def hash_clave(clave: str) -> str:
    sal = secrets.token_bytes(16)
    h = hashlib.scrypt(clave.encode(), salt=sal, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${sal.hex()}${h.hex()}"


def verificar_clave(clave: str, almacenado: str) -> bool:
    try:
        _, n, r, p, sal, esperado = almacenado.split("$")
        h = hashlib.scrypt(clave.encode(), salt=bytes.fromhex(sal), n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(h.hex(), esperado)
    except Exception:
        return False


# Hash ficticio para gastar el mismo tiempo cuando el RUT no existe (evita enumerar usuarios).
HASH_SEÑUELO = hash_clave(secrets.token_hex(8))


# Lista de bloqueo (NIST SP 800-63B rev. 4): contraseñas comunes, filtradas o propias del contexto.
from establecimiento import EST  # noqa: E402

_BLOQUEADAS_ARCHIVO = Path(__file__).with_name("claves_bloqueadas.txt")
_BLOQUEADAS = {l.strip().lower() for l in _BLOQUEADAS_ARCHIVO.read_text(encoding="utf-8").splitlines()
               if l.strip() and not l.startswith("#")} if _BLOQUEADAS_ARCHIVO.exists() else set()
_CONTEXTO = ("hospital", "password", "contrasena", "contraseña", "clave", "store", "quillota", "chile",
             *(p.lower() for p in EST.get("palabras_contrasena", [])))


def problemas_clave(clave: str, rut: str, nombre: str = "") -> list[str]:
    """Política NIST: largo mínimo y lista de bloqueo; sin reglas de composición ni rotación forzada."""
    from config import CLAVE_LARGO_MAX, CLAVE_LARGO_MIN
    p = []
    if len(clave) < CLAVE_LARGO_MIN:
        p.append(f"Debe tener al menos {CLAVE_LARGO_MIN} caracteres. Una frase de varias palabras es fácil de recordar.")
    if len(clave) > CLAVE_LARGO_MAX:
        p.append(f"Puede tener hasta {CLAVE_LARGO_MAX} caracteres.")
    normal = re.sub(r"[\s._-]", "", clave.lower())
    cuerpo = rut.split("-")[0]
    if cuerpo in re.sub(r"\D", "", clave):
        p.append("No puede contener tu RUT.")
    if any(len(x) >= 4 and x in normal for x in (nombre or "").lower().split()):
        p.append("No puede contener tu nombre.")
    if clave.lower() in _BLOQUEADAS or normal in _BLOQUEADAS:
        p.append("Es una contraseña muy común o filtrada. Elige otra.")
    elif sum(len(c) for c in _CONTEXTO if c in normal) >= len(normal) * 0.6:
        p.append("Es demasiado parecida al nombre del hospital o del sistema.")
    if len(set(clave)) <= 3:
        p.append("Repite demasiado los mismos caracteres.")
    return p


def clave_temporal() -> str:
    alfabeto = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
    while True:
        c = "".join(secrets.choice(alfabeto) for _ in range(16))
        if re.search(r"\d", c) and re.search(r"[A-Za-z]", c):
            return c


# ---------------------------------------------------------------- tokens
def nuevo_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

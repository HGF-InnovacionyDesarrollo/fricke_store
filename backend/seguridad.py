"""RUT, contraseñas y tokens. Solo biblioteca estándar."""
import hashlib
import hmac
import re
import secrets


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


def problemas_clave(clave: str, rut: str, nombre: str = "") -> list[str]:
    from config import CLAVE_LARGO_MIN
    p = []
    if len(clave) < CLAVE_LARGO_MIN:
        p.append(f"Debe tener al menos {CLAVE_LARGO_MIN} caracteres.")
    if not re.search(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]", clave) or not re.search(r"\d", clave):
        p.append("Debe combinar letras y números.")
    cuerpo = rut.split("-")[0]
    if cuerpo in re.sub(r"\D", "", clave):
        p.append("No puede contener tu RUT.")
    for parte in (nombre or "").lower().split():
        if len(parte) >= 4 and parte in clave.lower():
            p.append("No puede contener tu nombre.")
            break
    return p


def clave_temporal() -> str:
    alfabeto = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
    while True:
        c = "".join(secrets.choice(alfabeto) for _ in range(12))
        if re.search(r"\d", c) and re.search(r"[A-Za-z]", c):
            return c


# ---------------------------------------------------------------- tokens
def nuevo_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

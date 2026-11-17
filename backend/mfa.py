"""Segundo factor de autenticación con códigos de 6 dígitos (TOTP, RFC 6238).

Funciona con Microsoft Authenticator (y cualquier app compatible: Google Authenticator, FreeOTP, Authy):
la persona escanea un código QR una vez y desde entonces la app le muestra un código que cambia cada 30 s.
No usa internet ni SMS. Es obligatorio para los perfiles privilegiados (ECO_MFA_PERFILES) y un administrador
puede exigirlo a cualquier otra persona desde el panel.
"""
import base64
import hashlib
import hmac
import io
import secrets
import struct
import time
from urllib.parse import quote

from cryptography.fernet import Fernet

import config as cfg

PASO = 30          # segundos que dura cada código
DIGITOS = 6
TOLERANCIA = 1     # acepta el código anterior y el siguiente (relojes desfasados hasta 30 s)
MAX_INTENTOS = 5   # códigos erróneos antes de cerrar la sesión pendiente
N_RESPALDO = 8


# ------------------------------------------------------------------ secreto (cifrado en la base)
def _fernet() -> Fernet:
    archivo = cfg.MFA_CLAVE_ARCHIVO
    if not archivo.exists():
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_bytes(Fernet.generate_key())
    return Fernet(archivo.read_bytes().strip())


def nuevo_secreto() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def cifrar(secreto: str) -> str:
    return _fernet().encrypt(secreto.encode()).decode()


def descifrar(guardado: str) -> str:
    return _fernet().decrypt(guardado.encode()).decode()


# ------------------------------------------------------------------ TOTP
def _codigo(secreto: str, paso: int) -> str:
    clave = base64.b32decode(secreto + "=" * (-len(secreto) % 8))
    h = hmac.new(clave, struct.pack(">Q", paso), hashlib.sha1).digest()
    o = h[-1] & 0x0F
    n = (struct.unpack(">I", h[o:o + 4])[0] & 0x7FFFFFFF) % 10 ** DIGITOS
    return str(n).zfill(DIGITOS)


def verificar(secreto: str, codigo: str, ultimo_paso: int | None) -> int | None:
    """Devuelve el paso usado si el código es válido y no se había usado antes; si no, None."""
    codigo = "".join(ch for ch in codigo if ch.isdigit())
    if len(codigo) != DIGITOS:
        return None
    actual = int(time.time()) // PASO
    for paso in range(actual - TOLERANCIA, actual + TOLERANCIA + 1):
        if hmac.compare_digest(_codigo(secreto, paso), codigo) and (ultimo_paso is None or paso > ultimo_paso):
            return paso
    return None


def uri(secreto: str, rut: str) -> str:
    """Dirección otpauth:// que lee Microsoft Authenticator al escanear el QR."""
    emisor = cfg.NOMBRE_PRODUCTO
    return (f"otpauth://totp/{quote(emisor)}:{quote(rut)}?secret={secreto}&issuer={quote(emisor)}"
            f"&algorithm=SHA1&digits={DIGITOS}&period={PASO}")


def qr_svg(texto: str) -> str:
    import qrcode
    import qrcode.image.svg
    img = qrcode.make(texto, image_factory=qrcode.image.svg.SvgPathImage, box_size=8, border=2)
    buf = io.BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode()
    return svg[svg.index("<svg"):]  # sin la declaración XML: va dentro del HTML


# ------------------------------------------------------------------ códigos de respaldo
def nuevos_codigos_respaldo() -> list[str]:
    """Códigos de un solo uso por si se pierde el celular (formato XXXX-XXXX, sin letras confusas)."""
    alfabeto = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return ["-".join("".join(secrets.choice(alfabeto) for _ in range(4)) for _ in range(2)) for _ in range(N_RESPALDO)]


def hash_respaldo(codigo: str) -> str:
    return hashlib.sha256(codigo.upper().replace("-", "").replace(" ", "").encode()).hexdigest()


def exigido(usuario) -> bool:
    """Obligatorio por perfil (privilegiados) o porque un administrador lo exigió a esta persona."""
    return usuario["rol"] in cfg.MFA_PERFILES or bool(usuario["mfa_exigido"])

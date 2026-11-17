"""Lo que nunca debe llegar al repositorio: datos, bases, claves ni secretos."""
import re
import subprocess

from conftest import RAIZ


def archivos_versionados() -> list[str]:
    salida = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True,
                            stdin=subprocess.DEVNULL).stdout
    return [l for l in salida.splitlines() if l]


def test_sin_datos_bases_ni_claves():
    prohibidos = [f for f in archivos_versionados()
                  if f.startswith("data/") or re.search(r"\.(db|sqlite3?|key|pem|pfx|p12|dump|enc|env)$|(^|/)\.env", f)]
    assert prohibidos == [], f"Archivos que no deben subirse: {prohibidos}"


def test_sin_secretos_en_el_codigo():
    patrones = [r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"ghp_[A-Za-z0-9]{30,}", r"sk-[A-Za-z0-9]{32,}",
                r"postgres(?:ql)?://[^:\s]+:(?!fricke_desarrollo@)[^@\s]{6,}@"]
    hallazgos = []
    for f in archivos_versionados():
        if not re.search(r"\.(py|js|html|css|md|txt|yml|yaml|json|sql|bat|toml|cfg|ini)$", f):
            continue
        texto = (RAIZ / f).read_text(encoding="utf-8", errors="ignore")
        hallazgos += [f"{f}: {p}" for p in patrones if re.search(p, texto)]
    assert hallazgos == [], f"Posibles secretos en el repositorio: {hallazgos}"

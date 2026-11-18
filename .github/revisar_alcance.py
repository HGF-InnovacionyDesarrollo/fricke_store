"""Revisa que un pull request de un colaborador toque solo su módulo y no la base del sistema.

Los colaboradores pueden cambiar únicamente:
  modulos/<clave>/...            el código del módulo
  docs/logo/modulos/<nombre>/... su logo
  frontend/img/modulos/<nombre>.svg  su ícono
Todo lo demás (backend/, frontend/, docs/, tests/, .github/, AGENTS.md, etc.) es la base del sistema y solo lo
cambian las cuentas de .github/mantenedores.txt.

Uso: python .github/revisar_alcance.py <autor> <commit_base> <commit_cambio>
"""
import re
import subprocess
import sys
from pathlib import Path

PERMITIDOS = (
    re.compile(r"^modulos/[a-z0-9_]+/.+"),
    re.compile(r"^docs/logo/modulos/[a-z0-9_-]+/[^/]+$"),
    re.compile(r"^frontend/img/modulos/[a-z0-9_-]+\.svg$"),
)


def mantenedores() -> set[str]:
    texto = Path(__file__).with_name("mantenedores.txt").read_text(encoding="utf-8")
    return {l.strip().lower() for l in texto.splitlines() if l.strip() and not l.startswith("#")}


def main() -> int:
    autor, base, cambio = sys.argv[1:4]
    if autor.lower() in mantenedores():
        print(f"{autor} es mantenedor del sistema: puede cambiar la base.")
        return 0
    archivos = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{cambio}"], capture_output=True, text=True, check=True
    ).stdout.split("\n")
    fuera = [a for a in archivos if a and not any(p.match(a) for p in PERMITIDOS)]
    modulos = {a.split("/")[1] for a in archivos if a.startswith("modulos/")}
    if fuera:
        print("Este pull request cambia la base del sistema, y eso solo lo hace la Unidad de Innovación y Desarrollo.")
        print("Como colaborador puedes cambiar solo modulos/<clave>/ y el ícono de tu módulo. Archivos fuera de tu módulo:")
        for a in fuera:
            print(f"  - {a}")
        print("Quita esos cambios de tu rama. Si de verdad necesitas un cambio común, pídelo a la Unidad.")
        return 1
    if len(modulos) > 1:
        print(f"Aviso: este pull request toca varios módulos ({', '.join(sorted(modulos))}). Lo normal es uno por entrega.")
    print("Alcance correcto: el pull request solo cambia módulos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

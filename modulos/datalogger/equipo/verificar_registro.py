"""Verifica las firmas de los registros del Monitor T/H.

Cada fila de datos y de eventos termina en una firma HMAC-SHA256 (16 hex)
calculada sobre la firma de la fila anterior del mismo registro + el resto de la
fila. Si alguien edita, borra o inserta filas, la cadena se rompe en ese punto.

Formatos que reconoce (la cadena sigue de uno al otro sin cortes):
  - actual:  datos/AAAA-MM-DD.csv y eventos/AAAA-MM-DD.csv, separados por ';'
  - antiguo: datos-AAAA-MM-DD.csv y eventos-AAAA-MM-DD.csv en la raíz, por ','

Ojo: si el archivo se abre en Excel y se guarda, Excel lo reescribe y las firmas
dejan de coincidir. Verificar siempre sobre los archivos originales de la SD.

La clave se obtiene enviando CLAVE por el monitor serie del C6.

Uso:
    python verificar_registro.py --clave <64 hex> <carpeta de la SD>
"""

import argparse
import hashlib
import hmac
import sys
from pathlib import Path

CEROS = "0" * 16


def firma(clave: bytes, previa: str, cuerpo: str) -> str:
    return hmac.new(clave, (previa + cuerpo).encode("utf-8"), hashlib.sha256).hexdigest()[:16]


def archivos_de(carpeta: Path, registro: str) -> list[tuple[str, Path]]:
    """Archivos de un registro en orden cronológico; el mismo día, el formato antiguo primero."""
    encontrados = [(f.name[len(registro) + 1:-4], 0, f) for f in carpeta.glob(f"{registro}-*.csv")]
    encontrados += [(f.stem, 1, f) for f in (carpeta / registro).glob("*.csv")]
    return [(f"{f.parent.name}/{f.name}" if orden else f.name, f) for _, orden, f in sorted(encontrados)]


def verificar(clave: bytes, archivos: list[tuple[str, Path]], nombre: str) -> int:
    """Devuelve la cantidad de problemas encontrados en la cadena."""
    if not archivos:
        print(f"{nombre}: no hay archivos")
        return 0

    previa = None
    filas = problemas = 0
    for etiqueta, archivo in archivos:
        lineas = archivo.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        if not lineas:
            continue
        separador = ";" if ";" in lineas[0] else ","
        for n, linea in enumerate(lineas[1:], start=2):  # la 1 es el encabezado
            if not linea.strip():
                continue
            cuerpo, _, firmada = linea.rpartition(separador)
            filas += 1
            if previa is None:
                # Primera fila: se acepta como inicio, salvo que sea el comienzo absoluto.
                if firma(clave, CEROS, cuerpo) != firmada:
                    print(f"  {etiqueta}:{n}  inicio de la cadena (no se puede verificar la fila anterior)")
            elif firma(clave, previa, cuerpo) != firmada:
                problemas += 1
                print(f"  {etiqueta}:{n}  FIRMA INVALIDA: fila modificada, o faltan/sobran filas antes de esta")
            previa = firmada

    estado = "OK" if problemas == 0 else f"{problemas} PROBLEMA(S)"
    print(f"{nombre}: {filas} filas en {len(archivos)} archivo(s) -> {estado}")
    return problemas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--clave", required=True, help="clave de firma en hex (comando CLAVE por serie)")
    parser.add_argument("carpeta", type=Path, help="carpeta con los CSV (raíz de la micro SD)")
    args = parser.parse_args()

    try:
        clave = bytes.fromhex(args.clave)
    except ValueError:
        print("La clave debe ser hexadecimal")
        return 2
    if len(clave) != 32:
        print("La clave debe tener 64 caracteres hex")
        return 2

    problemas = verificar(clave, archivos_de(args.carpeta, "datos"), "Datos")
    problemas += verificar(clave, archivos_de(args.carpeta, "eventos"), "Eventos")
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())

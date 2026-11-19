"""Copia el firmware compilado a configurador/firmware/ para incluirlo en el .exe.

Desde el firmware 2.5 hay una sola compilación para todas las placas (4 y 8 MB), con la
división de memoria de ../partitions.csv (una sola app de 2,5 MB). Se compila con:

  arduino-cli compile --fqbn esp32:esp32:esp32c6:FlashSize=4M,PartitionScheme=custom,ZigbeeMode=zczr,DebugLevel=info,CDCOnBoot=cdc ^
      --build-property upload.maximum_size=2621440 --build-path <carpeta> <carpeta del sketch llamada Monitor_TH>

Uso:  python preparar_firmware.py <carpeta de compilación>
"""
import hashlib
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(AQUI, "firmware")
TOPE_APP = 0x280000  # tamaño de app0 en ../partitions.csv
ARCHIVOS = {  # en la carpeta de compilación -> nombre en firmware/
    "Monitor_TH.ino.bootloader.bin": "bootloader.bin",
    "Monitor_TH.ino.partitions.bin": "partitions.bin",
    "boot_app0.bin": "boot_app0.bin",
    "Monitor_TH.ino.bin": "Monitor_TH.bin",
}


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    origen = sys.argv[1]
    faltan = [a for a in ARCHIVOS if not os.path.isfile(os.path.join(origen, a))]
    if faltan:
        print(f"Faltan en '{origen}': {', '.join(faltan)}")
        return 1
    tam = os.path.getsize(os.path.join(origen, "Monitor_TH.ino.bin"))
    if tam > TOPE_APP:
        print(f"El programa pesa {tam} bytes y no cabe en la partición de {TOPE_APP} bytes.")
        return 1
    with open(os.path.join(AQUI, "..", "Monitor_TH.ino"), encoding="utf-8") as f:
        version = re.search(r'#define VERSION_FIRMWARE "([^"]+)"', f.read()).group(1)
    os.makedirs(DESTINO, exist_ok=True)
    # carpetas de cuando había una compilación por tamaño de flash (8MB/ y 4MB/)
    for viejo in ("8MB", "4MB"):
        shutil.rmtree(os.path.join(DESTINO, viejo), ignore_errors=True)
    sumas = []
    for a, b in ARCHIVOS.items():
        shutil.copyfile(os.path.join(origen, a), os.path.join(DESTINO, b))
        with open(os.path.join(DESTINO, b), "rb") as f:
            sumas.append(f"{hashlib.sha256(f.read()).hexdigest()}  {b}")
    with open(os.path.join(DESTINO, "version.txt"), "w", encoding="utf-8") as f:
        f.write(version + "\n")
    with open(os.path.join(DESTINO, "SHA256SUMS.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(sumas) + "\n")
    print(f"Firmware {version} copiado a {DESTINO} ({tam} bytes, {100 * tam // TOPE_APP} % de la partición)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

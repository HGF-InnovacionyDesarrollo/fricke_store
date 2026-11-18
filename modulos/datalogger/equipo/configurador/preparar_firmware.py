"""Copia el firmware compilado a configurador/firmware/ para incluirlo en el .exe.

Se incluyen dos compilaciones del mismo código, una por tamaño de flash de la placa
(el Configurador detecta la flash e instala la que corresponde):

  firmware/8MB/  FQBN esp32:esp32:esp32c6:FlashSize=8M,PartitionScheme=zigbee_zczr_8MB,ZigbeeMode=zczr,DebugLevel=info,CDCOnBoot=cdc
  firmware/4MB/  FQBN esp32:esp32:esp32c6:FlashSize=4M,PartitionScheme=zigbee_zczr,ZigbeeMode=zczr,DebugLevel=info,CDCOnBoot=cdc

Uso:  python preparar_firmware.py <compilación 8 MB> <compilación 4 MB>
"""
import hashlib
import os
import re
import shutil
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(AQUI, "firmware")
ARCHIVOS = {  # en la carpeta de compilación -> nombre en firmware/<tamaño>/
    "Monitor_TH.ino.bootloader.bin": "bootloader.bin",
    "Monitor_TH.ino.partitions.bin": "partitions.bin",
    "boot_app0.bin": "boot_app0.bin",
    "Monitor_TH.ino.bin": "Monitor_TH.bin",
}


def main() -> int:
    origenes = dict(zip(("8MB", "4MB"), sys.argv[1:3]))
    if len(origenes) != 2:
        print(__doc__)
        return 1
    for tam, origen in origenes.items():
        faltan = [a for a in ARCHIVOS if not os.path.isfile(os.path.join(origen, a))]
        if faltan:
            print(f"Faltan en '{origen}' ({tam}): {', '.join(faltan)}")
            return 1
    with open(os.path.join(AQUI, "..", "Monitor_TH.ino"), encoding="utf-8") as f:
        version = re.search(r'#define VERSION_FIRMWARE "([^"]+)"', f.read()).group(1)
    sumas = []
    for tam, origen in origenes.items():
        carpeta = os.path.join(DESTINO, tam)
        os.makedirs(carpeta, exist_ok=True)
        for a, b in ARCHIVOS.items():
            shutil.copyfile(os.path.join(origen, a), os.path.join(carpeta, b))
            with open(os.path.join(carpeta, b), "rb") as f:
                sumas.append(f"{hashlib.sha256(f.read()).hexdigest()}  {tam}/{b}")
    # binarios sueltos de cuando había una sola compilación
    for b in ARCHIVOS.values():
        viejo = os.path.join(DESTINO, b)
        if os.path.isfile(viejo):
            os.remove(viejo)
    with open(os.path.join(DESTINO, "version.txt"), "w", encoding="utf-8") as f:
        f.write(version + "\n")
    with open(os.path.join(DESTINO, "SHA256SUMS.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(sumas) + "\n")
    print(f"Firmware {version} (8 MB y 4 MB) copiado a {DESTINO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

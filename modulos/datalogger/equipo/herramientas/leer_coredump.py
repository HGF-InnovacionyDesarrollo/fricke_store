"""Extrae PC/RA de cada tarea de un coredump ELF de ESP32-C6 (RISC-V) y busca
direcciones de código en su pila, para traducirlas con addr2line.

Sirve para saber dónde se colgó el firmware cuando un ARRANQUE dice "watchdog".

1. Leer la partición coredump de la placa (división de partitions.csv, firmware 2.5 o posterior;
   en placas con la división antigua de 8 MB estaba en 0x7F0000):
     esptool --port COM10 read_flash 0x3F0000 0x10000 coredump.bin
2. Usar el .elf de la MISMA versión de firmware que estaba corriendo:
     python leer_coredump.py coredump.bin Monitor_TH.ino.elf riscv32-esp-elf-addr2line.exe
   (addr2line está en Arduino15\\packages\\esp32\\tools\\esp-rv32\\<versión>\\bin)
"""
import struct
import subprocess
import sys

dump, elf, addr2line = sys.argv[1], sys.argv[2], sys.argv[3]
data = open(dump, "rb").read()
inicio = data.find(b"\x7fELF")
e = data[inicio:]

(e_phoff,) = struct.unpack_from("<I", e, 28)
e_phentsize, e_phnum = struct.unpack_from("<HH", e, 42)
segmentos, notas = [], []
for i in range(e_phnum):
    p_type, p_offset, p_vaddr, _, p_filesz, _, _, _ = struct.unpack_from("<8I", e, e_phoff + i * e_phentsize)
    if p_type == 1:
        segmentos.append((p_vaddr, e[p_offset:p_offset + p_filesz]))
    elif p_type == 4:
        notas.append(e[p_offset:p_offset + p_filesz])


def leer_mem(addr, n):
    for base, blob in segmentos:
        if base <= addr and addr + n <= base + len(blob):
            return blob[addr - base:addr - base + n]
    return None


def es_codigo(v):
    return 0x42000000 <= v < 0x42800000 or 0x40800000 <= v < 0x40880000


tareas = []
for blob in notas:
    off = 0
    while off + 12 <= len(blob):
        namesz, descsz, ntype = struct.unpack_from("<3I", blob, off)
        name = blob[off + 12:off + 12 + namesz].rstrip(b"\0").decode(errors="replace")
        doff = off + 12 + ((namesz + 3) & ~3)
        desc = blob[doff:doff + descsz]
        if ntype == 1 and descsz >= 72 + 12:  # NT_PRSTATUS
            tcb = struct.unpack_from("<I", desc, 24)[0]
            pc, ra, sp = struct.unpack_from("<3I", desc, 72)
            tareas.append((tcb, pc, ra, sp))
        off = doff + ((descsz + 3) & ~3)


def nombre_tarea(tcb):
    # En FreeRTOS el nombre (pcTaskName) está dentro del TCB; se busca texto imprimible.
    mem = leer_mem(tcb, 0x60) or b""
    mejor = ""
    for i in range(0, len(mem) - 4):
        s = mem[i:i + 16].split(b"\0")[0]
        if len(s) >= 4 and all(32 <= c < 127 for c in s) and len(s) > len(mejor):
            mejor = s.decode()
    return mejor or hex(tcb)


def simbolo(addrs):
    if not addrs:
        return []
    out = subprocess.run([addr2line, "-pfiaC", "-e", elf] + [hex(a) for a in addrs], capture_output=True, text=True).stdout
    return out.strip().splitlines()


for tcb, pc, ra, sp in tareas:
    nombre = nombre_tarea(tcb)
    print(f"=== Tarea {nombre}  pc={pc:#x} ra={ra:#x} sp={sp:#x}")
    candidatos = [pc, ra]
    pila = leer_mem(sp, 1024) or b""
    for i in range(0, len(pila) - 3, 4):
        v = struct.unpack_from("<I", pila, i)[0]
        if es_codigo(v) and v not in candidatos:
            candidatos.append(v)
    for linea in simbolo(candidatos[:24]):
        print("   ", linea)

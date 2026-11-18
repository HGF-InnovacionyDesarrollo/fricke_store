# Caja impresa del Monitor T/H

Caja para colgar en la pared, pantalla vertical. Diseño paramétrico en Blender:
`caja_monitor.py` tiene todas las medidas al principio y genera las piezas; los
STL quedan en `stl/` (unidades en mm).

## Cómo regenerar

En Blender (con el complemento MCP o desde Scripting):

```python
ruta = r"C:\Users\usuariohgf\Documents\Desarrollos\Monitor_TH\caja\caja_monitor.py"
g = {"__name__": "caja", "__file__": ruta}
exec(open(ruta, encoding="utf-8").read(), g)
g["construir_todo"]()      # piezas + modelos de referencia (colección "Referencia")
g["exportar_stl"]()        # stl/cuerpo.stl, stl/tapa.stl, stl/boton.stl
```

Las funciones no persisten entre ejecuciones: volver a hacer el `exec` cada vez.

## Piezas

| Pieza | Descripción |
|---|---|
| Cuerpo | Fondo + 4 paredes, abierto adelante. 81 × 105 × 42,5 mm (84,5 de ancho con reborde de SD y aro del botón) |
| Tapa | Frente: ventana de la pantalla con bisel a 45°, rebaje para el vidrio, 4 postes M2, rejilla y anillo del buzzer, guías del módulo SD |
| Boton | Botón impreso que empuja el pulsador desde el costado derecho |

## Distribución (acordada con el usuario)

- Montaje: opción A. Placa de conexiones de 4 × 4 cm solo para conexiones; el
  ESP32 va aparte, con cables dupont, fijado con cinta doble contacto de 3 mm.
- Pantalla al frente, centrada, con los pines arriba.
- Pulsador en el costado derecho, a media altura, hundido 1,5 mm con aro.
- SD accesible desde afuera por el costado izquierdo (lector de fricción: la
  tarjeta insertada sobresale 7,5 mm del lector; queda asomando ~5 mm).
- USB-C por abajo. ESP32 vertical con USB abajo y antena arriba, libre.
- Placa 4 × 4 y RTC en el fondo, lado derecho. Buzzer al frente bajo la pantalla.
- Dos ojos de cerradura atrás. Ventilación en los costados. Tapa con 4 M3.

## Medidas de los componentes (de fotos con regla, ±1 mm)

| Componente | Medida |
|---|---|
| ESP32-C6 DevKitC clon (2 USB-C, pines soldados hacia abajo) | Placa ~55 × 25,4; total 64,5 con antena (+7,5) y USB (+2) |
| Pantalla 1,9" 170×320 EstarDyn | Placa 29 × 62; vidrio 25,8 × 49,7; área visible 22,7 × 42,7; agujeros M2 a 25 × 57,5; **vidrio a placa 2,5 mm (medido)** |
| Módulo micro SD 3,3 V (6 pines) | ~20 × 17 (con el lector, que sobresale 2,5 del PCB) |
| RTC DS3231 (ZS-042) | 38 × 22 × 14 |
| Pulsador TS0719 | 12 × 12 × 7,3 |
| Buzzer pasivo | ~12 mm de diámetro (sin confirmar) |

## Impresión

PETG. Cuerpo apoyado en el fondo, tapa con la cara frontal en la cama, botón con la
pestaña en la cama; sin soportes. Relleno 20 %, 3 perímetros, capa 0,2 mm.
Tornillos: 4 × M3×10 autorroscantes (tapa), 8 × M2×5-6 autorroscantes (pantalla
y placa 4 × 4), 2 tornillos de pared con cabeza ≤ 8 mm.

## Pendiente

1. Imprimir solo la tapa y comprobar la ventana, el vidrio y los agujeros de la
   pantalla antes de imprimir el cuerpo.
2. Confirmar el diámetro del buzzer.
3. Ajustar lo que no calce y regenerar.

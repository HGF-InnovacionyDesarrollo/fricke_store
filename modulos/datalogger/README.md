# Data+ (data logger)

Recibe y muestra la información de los data logger del hospital. Hoy son los **Monitor T/H** (temperatura y humedad
con sensores Zigbee, proyecto `Monitor_TH` de la Unidad de Innovación y Desarrollo), que graban en su tarjeta SD.

Pedido por: Unidad de Innovación y Desarrollo (nov 2026). Familia 4, Operaciones y equipos. Pictograma `thermometer`
de Lucide.

## Qué hace

| Pantalla | Para qué |
|---|---|
| Resumen | Último valor de cada sensor con su estado (en rango, atención, alarma), batería baja, sensor sin reportar y fecha de la última importación. |
| Detalle de un sensor | Gráfico de temperatura y humedad con el rango normal y los límites de alarma; mínimo, máximo, promedio, temperatura cinética media (MKT), tiempo sin alarma, registro completo y huecos. Descarga en CSV e informe para imprimir. |
| Alarmas | Períodos fuera del rango de alarma, calculados desde las mediciones, con su duración y valor extremo. Quien tenga el permiso registra la revisión y la acción tomada (no se edita después). |
| Sensores | Código, serie y firmware de cada equipo; ubicación y estado de cada sensor. |
| Eventos | Registro de los equipos: arranques, alarmas, cortes de luz, tarjeta SD, calibración, etc. |
| Archivos | Quién importó qué, cuántas mediciones eran nuevas y si las firmas estaban correctas. |

Rangos por tipo de almacenamiento (los mismos del firmware): **Medicamentos** (APF 1.5) normal 16 a 24 °C, alarma bajo
15 o sobre 30 °C, humedad normal hasta 55 %, alarma sobre 60 %; **Material estéril** (APE 1.4) normal 19 a 23 °C,
alarma bajo 18 o sobre 24 °C, humedad normal 33 a 47 %, alarma bajo 30 o sobre 50 %.

## Cómo llegan los datos

Los Monitor T/H no tienen red. Se importan los CSV de las carpetas `datos/` y `eventos/` de la tarjeta SD
(*Importar archivos*). El módulo:

- reconoce los tres formatos del firmware (con y sin columna Monitor, y los antiguos separados por coma);
- convierte la hora del equipo a UTC con la misma regla de horario de verano del firmware;
- no duplica lo que ya se importó (una medición por sensor y hora);
- con la **clave de firma** del equipo (comando `CLAVE` por USB), verifica la cadena HMAC-SHA256 de cada registro y
  dice qué filas se editaron, borraron o insertaron. La clave no se guarda ni va a la bitácora.

Límite conocido: en la hora repetida del cambio a horario de invierno (primer sábado de abril), las mediciones de esa
hora se toman como repetidas.

## Permisos

| Permiso | Funcionario | Administrador |
|---|---|---|
| `datalogger.ver` | Sí | Sí |
| `datalogger.importar` | | Sí |
| `datalogger.revisar` | | Sí |
| `datalogger.configurar` | | Sí |

A los encargados de Farmacia, Esterilización o Calidad se les otorgan uno a uno, por ejemplo:
`python backend/gestionar.py permiso --rut … --permiso datalogger.revisar`.

## Datos personales (Ley 21.719)

Las mediciones no son datos personales. Guarda el id interno del funcionario que importa y del que revisa una
alarma, con la acción que escribió. Conservación: 5 años (lo aplica `depurar()`); `exportar_titular()` entrega lo
de cada persona en *Mi cuenta › Descargar mis datos*.

## Pendiente (pedir a la Unidad de Innovación y Desarrollo)

- **Envío automático desde los equipos** (etapa 3 del Monitor T/H, por WiFi o LoRaWAN): necesita una credencial de
  equipo común en el portal, porque hoy todo endpoint exige la sesión de una persona.
- **Avisos de alarma** por correo u otro canal: necesita el servicio común de avisos.
- Aviso de calibración vencida (12 meses, APF 1.5) cuando los equipos informen la fecha de calibración en sus archivos.

## Probar

```bash
pytest modulos/datalogger
```

Para verlo: *Administración › Módulos › Data+*, marcar *Activo* y elegir los perfiles. Luego importar los CSV de
`Monitor_TH/respaldo_sd/`.

#pragma once
// Configuración inicial de los monitores que existían antes del firmware 2.0.
//
// Desde la 2.0 la configuración de cada monitor (código, pantalla, buzzer y sensores)
// vive en la memoria de su placa y se cambia por USB con el Configurador
// (configurador/ConfiguradorMonitorTH.exe), sin compilar. Esta tabla solo se usa la
// primera vez que una placa arranca con la 2.0 y todavía no tiene configuración: si
// su número de serie está aquí, parte con estos valores (los que tenía en config.h);
// si no, parte como "MTH-NUEVO", pantalla 1,9" y sin sensores.
//
// Sensores: "ieee4|nombre|perfil|corrT|corrH|calibrado|oculto" separados por ';'
// (mismo formato que el comando @SENSOR_SET). perfil: MED o EST.

struct ConfigInicial {
  const char *serie;
  const char *codigo;
  uint8_t pantalla;     // 1 = 1,9" 170x320 | 2 = 2,4" 240x320
  uint8_t buzzerTemp;   // 1 = las alarmas de temperatura suenan
  uint8_t buzzerHum;    // 1 = las alarmas de humedad suenan
  const char *sensores;
};

static const ConfigInicial CONFIG_INICIAL[] = {
  // MTH-01: prueba funcional en Esterilización (desde 2026-10-13); calibración de
  // temperatura del 2026-10-08 (docs/Anexo1_calibracion_MTH-01_2026-10.docx).
  {"98A316FFFE9BB2EC", "MTH-01", 1, 0, 0,
   "FFFF|Bodega Esteril|EST|0.2|0|2026-10-08 (solo T)|0;"
   "D314|Medicamentos 3|MED|0.0|0|2026-10-08 (solo T)|1;"
   "00E4|Medicamentos 2|MED|0.1|0|2026-10-08 (solo T)|1"},
  // MTH-02 (desde 2026-11-04): sensor 00E4 traído del MTH-01, con su calibración.
  {"98A316FFFE9BB340", "MTH-02", 2, 1, 0,
   "00E4|Medicamentos 2|MED|0.1|0|2026-10-08 (solo T)|0"},
};

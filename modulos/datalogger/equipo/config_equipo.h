#pragma once
// Configuración de cada equipo, guardada en la NVS de la placa (firmware 2.0).
// Se cambia por USB con el Configurador (configurador/protocolo.md).
#include "config.h"

#define CONFIG_VERSION 1
struct SensorCfg {
  char ieee4[5];        // últimos 4 caracteres de la IEEE ("00E4")
  char nombre[31];      // sin tildes ni | " ;
  uint8_t perfil;       // 0 = MEDICAMENTOS, 1 = MATERIAL ESTERIL
  uint8_t oculto;       // 1 = fuera de servicio: se ignora
  int16_t corrT10;      // corrección de temperatura, décimas de °C
  int16_t corrH;        // corrección de humedad, %HR
  char calibrado[24];   // "2026-10-08 (solo T)", "" = sin calibración registrada
};
struct ConfigEquipo {
  uint8_t version;
  char codigo[16];
  uint8_t pantalla;     // 1 = 1,9" 170x320 | 2 = 2,4" 240x320
  uint8_t buzzerTemp;   // 1 = las alarmas de temperatura suenan
  uint8_t buzzerHum;    // 1 = las alarmas de humedad suenan
  uint8_t nSensores;
  SensorCfg sensores[MAX_SENSORES];
};

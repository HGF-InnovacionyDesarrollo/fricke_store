// Monitor de temperatura y humedad Zigbee
// ESP32-C6 como coordinador Zigbee + pantalla ST7789 170x320.
//
// Configuración en Arduino IDE (Herramientas):
//   Placa:           ESP32C6 Dev Module
//   Zigbee mode:     Zigbee ZCZR (coordinator/router)
//   Flash Size:      8MB
//   Partition Scheme: Zigbee ZCZR 8MB with spiffs
//   USB CDC On Boot: Enabled
//   Core Debug Level: Info (muestra en serie cuando se une un dispositivo)

#include <Arduino.h>
#ifndef ZIGBEE_MODE_ZCZR
#error "Selecciona Herramientas > Zigbee mode > Zigbee ZCZR (coordinator/router)"
#endif

#include "Zigbee.h"
#include <Arduino_GFX_Library.h>
#include <Preferences.h>
#include <SD.h>
#include <LittleFS.h>
#include <Wire.h>
#include <time.h>
#include <sys/time.h>
#include <stdarg.h>
#include "mbedtls/md.h"
#include "esp_task_wdt.h"
#include "esp_mac.h"
#include "driver/gpio.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_coexist.h"
#include "config.h"
#include "config_equipo.h"
#include "config_inicial.h"
#include "logo_pantalla.h"      // LOGO_PANTALLA_170: F+data + "Funciona con" Fricke Store (1,9")
#include "logo_pantalla_240.h"  // LOGO_PANTALLA_240 (pantalla 2,4")
#include "logo_marca.h"         // MARCA_*: ícono de F+data de 24 px, siempre en la cabecera

#define VERSION_FIRMWARE "2.5"  // subir al cambiar el comportamiento; queda en el evento ARRANQUE
#define LARGO_LINEA  200  // largo máximo de una fila de registro (incluida la firma)
#define COLA_EVENTOS 24   // eventos en espera de escribirse

// El watchdog de loop() se activa al final de setup(); alimentarlo antes solo llena
// el monitor serie de errores "task not found".
static bool wdtActivo = false;
#define alimentarWDT() do { if (wdtActivo) feedLoopWDT(); } while (0)  // macro: una función aquí rompe los prototipos del .ino

// ======================= Sensores =======================

struct Sensor {
  bool usado;
  uint8_t ieee[8];
  uint16_t shortAddr;  // 0xFFFF = desconocida
  uint8_t endpoint;    // 0 = desconocido
  bool tieneTemp;
  bool tieneHum;
  float temp;
  float hum;
  bool enAlarma;       // temperatura fuera del rango de su perfil
  bool enAlarmaHum;    // humedad fuera del rango de su perfil
  uint32_t alarmaTempDesde;  // hora unix en que empezó cada alarma (0 = desconocida)
  uint32_t alarmaHumDesde;
  uint32_t ultimoMs;
  bool tieneBat;
  uint8_t bat;         // % mostrado (suavizado)
  bool batPorVoltaje;  // estimado por voltaje (el sensor no informó porcentaje)
  uint32_t batMs;
  uint8_t batPico;          // máximo de la ventana actual
  uint8_t batPicoAnterior;  // máximo de la ventana anterior
  uint32_t batVentanaMs;    // inicio de la ventana actual
  bool identificar;    // recién unido: falta leer fabricante/modelo
  bool configurado;    // en este arranque ya se enlazó la batería y se configuraron reportes
  bool despierto;      // acaba de reportar: buen momento para enviarle pedidos
  uint32_t ultimoPedidoBatMs;
  bool batGuardada;    // el % viene de la memoria (antes del reinicio), no del sensor todavía
  bool avisoSinDatos;  // aviso técnico: no reporta hace más de SIN_DATOS_MIN
  bool avisoBatBaja;   // aviso técnico: batería bajo BATERIA_BAJA
  bool reportoTrasArranque;  // ya llegó su primera lectura desde que arrancó el monitor
};

// Último valor de un sensor, guardado en la flash para que sobreviva a un reinicio.
struct UltimoValor {
  uint8_t ieee[8];
  float temp;
  float hum;
  uint32_t lectura;  // hora unix de la lectura
  uint8_t marcas;    // bit 0 tieneTemp, 1 tieneHum, 2 enAlarma, 3 enAlarmaHum
  uint32_t alarmaTempDesde;
  uint32_t alarmaHumDesde;
};

// CSV de la SD abierto para agregar filas, con el tamaño que debería tener al
// cerrarlo (para verificar que la escritura quedó realmente en la tarjeta).
struct CsvAbierto {
  File f;
  char ruta[32];
  size_t esperado;
};

static Sensor sensores[MAX_SENSORES];
static portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;
static volatile bool listaCambio = false;
static volatile bool alarmaCambio = false;
static uint32_t silencioHastaMs = 0;      // buzzer silenciado con el pulsador hasta
static uint64_t mascaraSilenciada = 0;    // alarmas que había al silenciar (bits)  // guardar los últimos valores ya, sin esperar el tramo
static volatile bool bateriaCambio = false;  // hay que guardar el % mostrado en memoria
static bool sinRed = false;                 // sin red eléctrica: el monitor funciona con el módulo UPS
static uint32_t sinRedDesdeMs = 0;
static uint32_t energiaMv = 0;              // último voltaje leído en ENERGIA_PIN (comando EQUIPO)
static bool energiaArmada = false;          // se vio alguna vez el divisor: la detección está activa

// ======================= Eventos =======================
// registrarEvento() se puede llamar desde cualquier tarea (también desde los
// callbacks de Zigbee): solo encola la línea; loop() la firma y la escribe.

static char colaEventos[COLA_EVENTOS][LARGO_LINEA];
static uint32_t colaMs[COLA_EVENTOS];  // millis() de cada evento (para fechar los que ocurren sin hora)
static int colaIni = 0, colaFin = 0;
static uint32_t eventosPerdidos = 0;
static uint8_t claveFirma[32];  // clave HMAC de las firmas del registro

static bool horaValida();

static void fechaActual(char *out) {
  if (!horaValida()) {
    strcpy(out, "0000-00-00 00:00:00");  // aún sin hora
    return;
  }
  time_t ahora = time(nullptr);
  struct tm t;
  localtime_r(&ahora, &t);
  strftime(out, 20, "%Y-%m-%d %H:%M:%S", &t);
}

static const char *codigoEquipo = "MTH-NUEVO";  // apunta a cfg.codigo al cargar la configuración
// Últimos eventos en memoria (comando @EVENTOS? del Configurador)
#define EVENTOS_RECIENTES 40
static char eventosRecientes[EVENTOS_RECIENTES][LARGO_LINEA];
static int eventosRecientesFin = 0, eventosRecientesN = 0;

static void registrarEvento(const char *tipo, const char *fmt, ...) {
  char detalle[110];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(detalle, sizeof(detalle), fmt, ap);
  va_end(ap);
  for (char *p = detalle; *p; p++) {
    if (*p == ';') *p = ',';                          // ';' es el separador de columnas
    else if (*p == '\n' || *p == '\r') *p = ' ';
  }
  char fecha[20];
  fechaActual(fecha);
  char linea[LARGO_LINEA];
  snprintf(linea, sizeof(linea), "%s;%s;%s;%s", fecha, codigoEquipo, tipo, detalle);
  Serial.printf("[EVENTO] %s\n", linea);

  portENTER_CRITICAL(&mux);
  memcpy(eventosRecientes[eventosRecientesFin], linea, LARGO_LINEA);
  eventosRecientesFin = (eventosRecientesFin + 1) % EVENTOS_RECIENTES;
  if (eventosRecientesN < EVENTOS_RECIENTES) eventosRecientesN++;
  int siguiente = (colaFin + 1) % COLA_EVENTOS;
  if (siguiente == colaIni) {
    eventosPerdidos++;
  } else {
    memcpy(colaEventos[colaFin], linea, LARGO_LINEA);
    colaMs[colaFin] = millis();
    colaFin = siguiente;
  }
  portEXIT_CRITICAL(&mux);
}

static void registrarLectura(esp_zb_zcl_addr_t src, uint8_t endpoint, float valor, bool esTemp);
static void registrarBateria(esp_zb_zcl_addr_t src, uint8_t endpoint, int pct, bool porVoltaje);

// Atributos del cluster Power Configuration (0x0001)
static const uint16_t ATTR_BATERIA_VOLT = 0x0020;  // unidades de 100 mV
static const uint16_t ATTR_BATERIA_PCT = 0x0021;   // medios %

// Los sensores envían temperatura, humedad y batería al mismo endpoint.
// ZigbeeThermostat se usa por su lógica de búsqueda y enlace de sensores, pero su
// zbAttributeRead ignora la batería, así que se reemplaza por uno que atiende los tres.
class ZigbeeMonitor : public ZigbeeThermostat {
public:
  ZigbeeMonitor(uint8_t endpoint) : ZigbeeThermostat(endpoint) {
    esp_zb_cluster_list_add_power_config_cluster(_cluster_list, esp_zb_zcl_attr_list_create(ESP_ZB_ZCL_CLUSTER_ID_POWER_CONFIG), ESP_ZB_ZCL_CLUSTER_CLIENT_ROLE);
  }

  void zbAttributeRead(uint16_t cluster_id, const esp_zb_zcl_attribute_t *attribute, uint8_t src_endpoint, esp_zb_zcl_addr_t src_address) override {
    const auto &d = attribute->data;
    if (!d.value) return;
    if (cluster_id == ESP_ZB_ZCL_CLUSTER_ID_TEMP_MEASUREMENT && attribute->id == ESP_ZB_ZCL_ATTR_TEMP_MEASUREMENT_VALUE_ID &&
        d.type == ESP_ZB_ZCL_ATTR_TYPE_S16) {
      registrarLectura(src_address, src_endpoint, *(int16_t *)d.value / 100.0f, true);
    } else if (cluster_id == ESP_ZB_ZCL_CLUSTER_ID_REL_HUMIDITY_MEASUREMENT && attribute->id == ESP_ZB_ZCL_ATTR_REL_HUMIDITY_MEASUREMENT_VALUE_ID &&
               d.type == ESP_ZB_ZCL_ATTR_TYPE_U16) {
      registrarLectura(src_address, src_endpoint, *(uint16_t *)d.value / 100.0f, false);
    } else if (cluster_id == ESP_ZB_ZCL_CLUSTER_ID_POWER_CONFIG && d.type == ESP_ZB_ZCL_ATTR_TYPE_U8) {
      uint8_t v = *(uint8_t *)d.value;
      if (v == 0xFF) return;  // valor inválido
      if (attribute->id == ATTR_BATERIA_PCT) {
        registrarBateria(src_address, src_endpoint, min(v / 2, 100), false);  // viene en medios %
      } else if (attribute->id == ATTR_BATERIA_VOLT) {
        // CR2032: ~3.0 V llena, ~2.1 V agotada (viene en unidades de 100 mV)
        registrarBateria(src_address, src_endpoint, constrain((v - 21) * 100 / 9, 0, 100), true);
      }
    }
  }
};

ZigbeeMonitor zbCoordinador = ZigbeeMonitor(1);
Preferences prefs;

static void ieeeATexto(const uint8_t *ieee, char *out) {
  sprintf(out, "%02X:%02X:%02X:%02X:%02X:%02X:%02X:%02X",
          ieee[7], ieee[6], ieee[5], ieee[4], ieee[3], ieee[2], ieee[1], ieee[0]);
}

// ======================= Configuración del equipo =======================
// Desde la 2.0 vive en la NVS de la placa (espacio "config") y se cambia por USB
// con el Configurador: comandos @EQUIPO_SET, @SENSOR_SET y @SENSOR_DEL (ver
// revisarComandoSerie). Cada cambio queda como evento CONFIG_*.
// Estructuras en config_equipo.h (en el .ino, Arduino declararía las funciones antes que ellas).
static ConfigEquipo cfg;
static const Perfil *const PERFILES[] = {&PERFIL_MEDICAMENTOS, &PERFIL_ESTERIL};
static const char *const PERFIL_CODIGO[] = {"MED", "EST"};
static char eventoConfigInicial[96] = "";  // se registra al arrancar (después de ARRANQUE)

static void guardarConfig() {
  Preferences p;
  p.begin("config", false);
  p.putBytes("equipo", &cfg, sizeof(cfg));
  p.end();
}

// Texto apto para la pantalla y el CSV: sin | " ; ni caracteres de control.
static void limpiarTexto(char *s) {
  for (; *s; s++)
    if (*s == '|' || *s == '"' || *s == ';' || *s == '\\' || (uint8_t)*s < 32 || (uint8_t)*s > 126) *s = ' ';
}

// "ieee4|nombre|MED|0.2|0|2026-10-08|0" -> SensorCfg. Devuelve un mensaje de error o nullptr.
static const char *parsearSensor(const char *txt, SensorCfg &s) {
  char buf[160];
  snprintf(buf, sizeof(buf), "%s", txt);
  char *campos[7] = {nullptr};
  int n = 0;
  char *p = buf;
  campos[n++] = p;
  while (*p && n < 7) {
    if (*p == '|') {
      *p = '\0';
      campos[n++] = p + 1;
    }
    p++;
  }
  if (n != 7) return "se esperan 7 campos separados por |";
  if (strlen(campos[0]) != 4) return "ieee4 debe tener 4 caracteres";
  for (int i = 0; i < 4; i++)
    if (!isxdigit((unsigned char)campos[0][i])) return "ieee4 debe ser hexadecimal";
  if (strlen(campos[1]) > 30) return "nombre de mas de 30 caracteres";
  float corrT = atof(campos[3]), corrH = atof(campos[4]);
  if (fabsf(corrT) > CORRECCION_MAX_TEMP) return "correccion de temperatura fuera del limite (3 C)";
  if (fabsf(corrH) > CORRECCION_MAX_HUM) return "correccion de humedad fuera del limite (15 %)";
  if (strlen(campos[5]) > 23) return "calibrado de mas de 23 caracteres";
  memset(&s, 0, sizeof(s));
  for (int i = 0; i < 4; i++) s.ieee4[i] = toupper((unsigned char)campos[0][i]);
  snprintf(s.nombre, sizeof(s.nombre), "%s", campos[1]);
  limpiarTexto(s.nombre);
  s.perfil = (strcasecmp(campos[2], "EST") == 0 || strcmp(campos[2], "1") == 0) ? 1 : 0;
  s.corrT10 = (int16_t)lroundf(corrT * 10);
  s.corrH = (int16_t)lroundf(corrH);
  snprintf(s.calibrado, sizeof(s.calibrado), "%s", campos[5]);
  limpiarTexto(s.calibrado);
  s.oculto = atoi(campos[6]) ? 1 : 0;
  return nullptr;
}

static int buscarSensorCfg(const char *ieee4) {
  for (int i = 0; i < cfg.nSensores; i++)
    if (strcasecmp(cfg.sensores[i].ieee4, ieee4) == 0) return i;
  return -1;
}

// Agrega o reemplaza un sensor en la configuración (en memoria). Copia breve con el
// mux tomado: las lecturas de Zigbee consultan esta tabla desde otra tarea.
static bool ponerSensorCfg(const SensorCfg &s) {
  int i = buscarSensorCfg(s.ieee4);
  if (i < 0 && cfg.nSensores >= MAX_SENSORES) return false;
  portENTER_CRITICAL(&mux);
  if (i < 0) i = cfg.nSensores++;
  cfg.sensores[i] = s;
  portEXIT_CRITICAL(&mux);
  return true;
}

// Carga la configuración de la NVS. La primera vez (o si cambió el formato) parte de
// config_inicial.h según el número de serie, o como equipo nuevo.
static void cargarConfig(const char *serie) {
  Preferences p;
  p.begin("config", true);
  bool ok = p.getBytesLength("equipo") == sizeof(cfg) && p.getBytes("equipo", &cfg, sizeof(cfg)) == sizeof(cfg) &&
            cfg.version == CONFIG_VERSION;
  p.end();
  if (!ok) {
    memset(&cfg, 0, sizeof(cfg));
    cfg.version = CONFIG_VERSION;
    const ConfigInicial *ini = nullptr;
    for (const ConfigInicial &c : CONFIG_INICIAL)
      if (strcmp(c.serie, serie) == 0) ini = &c;
    if (ini) {
      snprintf(cfg.codigo, sizeof(cfg.codigo), "%s", ini->codigo);
      cfg.pantalla = ini->pantalla;
      cfg.buzzerTemp = ini->buzzerTemp;
      cfg.buzzerHum = ini->buzzerHum;
      char lista[400];
      snprintf(lista, sizeof(lista), "%s", ini->sensores);
      for (char *tok = strtok(lista, ";"); tok; tok = strtok(nullptr, ";")) {
        SensorCfg s;
        if (!parsearSensor(tok, s)) ponerSensorCfg(s);
      }
      snprintf(eventoConfigInicial, sizeof(eventoConfigInicial), "configuracion de %s (de la version 1.x) con %d sensores",
               cfg.codigo, cfg.nSensores);
    } else {
      snprintf(cfg.codigo, sizeof(cfg.codigo), "MTH-NUEVO");
      cfg.pantalla = 1;
      cfg.buzzerTemp = 1;
      cfg.buzzerHum = 0;
      snprintf(eventoConfigInicial, sizeof(eventoConfigInicial),
               "equipo sin configuracion: MTH-NUEVO, pantalla 1,9\", sin sensores (usar el Configurador)");
    }
    guardarConfig();
  }
  if (cfg.pantalla != 2) cfg.pantalla = 1;
  if (cfg.nSensores > MAX_SENSORES) cfg.nSensores = 0;
  codigoEquipo = cfg.codigo;
}

// Configuración de ese sensor (nullptr si no está).
static const SensorCfg *configSensor(const uint8_t *ieee) {
  char fin[5];
  sprintf(fin, "%02X%02X", ieee[1], ieee[0]);
  int i = buscarSensorCfg(fin);
  return i < 0 ? nullptr : &cfg.sensores[i];
}

static void nombreSensor(int idx, const uint8_t *ieee, char *out, size_t len) {
  const SensorCfg *n = configSensor(ieee);
  if (n && n->nombre[0]) snprintf(out, len, "%s", n->nombre);
  else snprintf(out, len, "Sensor %d", idx + 1);
}

// Corrección configurada de un sensor (0 si excede el límite de seguridad).
static float correccionCfg(const SensorCfg *n, bool esTemp) {
  float v = esTemp ? n->corrT10 / 10.0f : (float)n->corrH;
  return fabsf(v) <= (esTemp ? CORRECCION_MAX_TEMP : CORRECCION_MAX_HUM) ? v : 0.0f;
}

// Corrección de calibración que se suma a la lectura (0 si no tiene).
static float correccionSensor(const uint8_t *ieee, bool esTemp) {
  const SensorCfg *n = configSensor(ieee);
  return n ? correccionCfg(n, esTemp) : 0;
}

static int contarSensores() {
  int n = 0;
  for (int i = 0; i < MAX_SENSORES; i++)
    if (sensores[i].usado) n++;
  return n;
}

// Sensor sacado de servicio ("oculto" en su configuración).
static bool sensorOculto(const uint8_t *ieee) {
  const SensorCfg *n = configSensor(ieee);
  return n && n->oculto;
}

static const Perfil &perfilSensor(const uint8_t *ieee) {
  const SensorCfg *n = configSensor(ieee);
  return n ? *PERFILES[n->perfil ? 1 : 0] : PERFIL_POR_DEFECTO;
}

// "rango 18.0-24.0 C", "maximo 60 %"... para eventos y pantalla.
static void rangoTexto(char *out, size_t len, float min, float max, bool esTemp) {
  const char *fmt = esTemp ? "%.1f" : "%.0f";
  char a[8], b[8];
  snprintf(a, sizeof(a), fmt, min);
  snprintf(b, sizeof(b), fmt, max);
  const char *u = esTemp ? "C" : "%";
  if (min <= SIN_LIMITE) snprintf(out, len, "maximo %s %s", b, u);
  else if (max <= SIN_LIMITE) snprintf(out, len, "minimo %s %s", a, u);
  else snprintf(out, len, "rango %s-%s %s", a, b, u);
}

// Devuelve el índice del sensor con esa IEEE, creándolo si hay espacio (-1 si no
// hay espacio o si está oculto en su configuración). Es el único lugar donde se crean
// sensores: aquí se filtran los ocultos para todos los caminos (reportes y la
// lista de enlazados que entrega la red al arrancar).
static int indiceSensor(const uint8_t *ieee, uint16_t shortAddr, uint8_t endpoint) {
  if (sensorOculto(ieee)) return -1;
  int idx = -1, libre = -1;
  bool nuevo = false;
  portENTER_CRITICAL(&mux);
  for (int i = 0; i < MAX_SENSORES; i++) {
    if (sensores[i].usado && memcmp(sensores[i].ieee, ieee, 8) == 0) {
      idx = i;
      break;
    }
    if (!sensores[i].usado && libre < 0) libre = i;
  }
  if (idx < 0 && libre >= 0) {
    idx = libre;
    memset(&sensores[idx], 0, sizeof(Sensor));
    sensores[idx].usado = true;
    sensores[idx].shortAddr = 0xFFFF;
    sensores[idx].identificar = true;
    memcpy(sensores[idx].ieee, ieee, 8);
    nuevo = true;
  }
  uint16_t direccionAnterior = 0xFFFF;
  if (idx >= 0) {
    if (!nuevo && shortAddr != 0xFFFF && sensores[idx].shortAddr != 0xFFFF && sensores[idx].shortAddr != shortAddr)
      direccionAnterior = sensores[idx].shortAddr;
    if (shortAddr != 0xFFFF) sensores[idx].shortAddr = shortAddr;
    if (endpoint != 0) sensores[idx].endpoint = endpoint;
  }
  portEXIT_CRITICAL(&mux);

  if (nuevo) {
    listaCambio = true;
    char txt[24];
    ieeeATexto(ieee, txt);
    Serial.printf("[NUEVO] Sensor %d  IEEE %s  short 0x%04X  ep %u\n", idx + 1, txt, shortAddr, endpoint);
    registrarEvento("SENSOR_NUEVO", "Sensor %d IEEE %s", idx + 1, txt);
  }
  if (direccionAnterior != 0xFFFF) {
    // Se volvió a unir a la red y el coordinador le dio otra dirección.
    char nombre[32];
    nombreSensor(idx, ieee, nombre, sizeof(nombre));
    registrarEvento("SENSOR_NUEVA_DIRECCION", "%s: 0x%04X -> 0x%04X (se volvio a unir a la red)", nombre,
                    direccionAnterior, shortAddr);
  }
  return idx;
}

// Copia la tabla de vecinos de la red (los sensores a pila son "hijos" del
// coordinador). Devuelve cuántos copió.
static int leerVecinos(esp_zb_nwk_neighbor_info_t *v, int max) {
  esp_zb_nwk_info_iterator_t it = ESP_ZB_NWK_INFO_ITERATOR_INIT;
  int n = 0;
  esp_zb_lock_acquire(portMAX_DELAY);
  while (n < max && esp_zb_nwk_get_next_neighbor(&it, &v[n]) == ESP_OK) n++;
  esp_zb_lock_release();
  return n;
}

// Resuelve el origen de un mensaje Zigbee a un índice de sensor (-1 si no se puede).
static int sensorDeOrigen(esp_zb_zcl_addr_t src, uint8_t endpoint) {
  uint8_t ieee[8];
  uint16_t sa = 0xFFFF;
  if (src.addr_type == ESP_ZB_ZCL_ADDR_TYPE_SHORT) {
    sa = src.u.short_addr;
    if (esp_zb_ieee_address_by_short(sa, ieee) != ESP_OK) {
      Serial.printf("Mensaje de 0x%04X sin IEEE conocida, se ignora\n", sa);
      return -1;
    }
  } else if (src.addr_type == ESP_ZB_ZCL_ADDR_TYPE_IEEE) {
    memcpy(ieee, src.u.ieee_addr, 8);
  } else {
    return -1;
  }
  if (sensorOculto(ieee)) return -1;  // fuera de servicio: se ignora
  int idx = indiceSensor(ieee, sa, endpoint);
  if (idx < 0) Serial.println("Se alcanzó MAX_SENSORES, mensaje ignorado");
  return idx;
}

// Compara el valor actual del sensor con el rango de su perfil y activa o apaga
// la alarma (con su evento). Se llama con cada lectura y al recuperar los últimos
// valores tras un reinicio (así un cambio de perfil se aplica sin esperar reporte).
static void evaluarAlarma(int idx, bool esTemp) {
  int cambioAlarma = 0;  // 1 = se activó, -1 = se apagó
  float valor = esTemp ? sensores[idx].temp : sensores[idx].hum;
  uint32_t ahora = horaValida() ? (uint32_t)time(nullptr) : 0;
  const Perfil &p = perfilSensor(sensores[idx].ieee);
  float min = esTemp ? p.tempMin : p.humMin, max = esTemp ? p.tempMax : p.humMax;
  float hist = esTemp ? ALARMA_HISTERESIS : ALARMA_HUM_HISTERESIS;
  bool fuera = valor > max || (min > SIN_LIMITE && valor < min);
  bool dentro = valor <= max - hist && (min <= SIN_LIMITE || valor >= min + hist);
  portENTER_CRITICAL(&mux);
  if (esTemp) {
    Sensor &s = sensores[idx];
    if (!s.enAlarma && fuera) {
      s.enAlarma = true;
      s.alarmaTempDesde = ahora;
      cambioAlarma = 1;
    } else if (s.enAlarma && dentro) {
      s.enAlarma = false;
      cambioAlarma = -1;
    }
  } else {
    Sensor &s = sensores[idx];
    if (!s.enAlarmaHum && fuera) {
      s.enAlarmaHum = true;
      s.alarmaHumDesde = ahora;
      cambioAlarma = 1;
    } else if (s.enAlarmaHum && dentro) {
      s.enAlarmaHum = false;
      cambioAlarma = -1;
    }
  }
  portEXIT_CRITICAL(&mux);
  if (cambioAlarma) {
    alarmaCambio = true;
    char nombre[32];
    nombreSensor(idx, sensores[idx].ieee, nombre, sizeof(nombre));
    const char *tipo = esTemp ? (cambioAlarma > 0 ? "ALARMA_TEMP" : "ALARMA_TEMP_FIN")
                              : (cambioAlarma > 0 ? "ALARMA_HUM" : "ALARMA_HUM_FIN");
    char rango[32];
    rangoTexto(rango, sizeof(rango), min, max, esTemp);
    if (esTemp) registrarEvento(tipo, "%s: %.1f C (%s %s)", nombre, valor, p.nombre, rango);
    else registrarEvento(tipo, "%s: %.0f %% HR (%s %s)", nombre, valor, p.nombre, rango);
  }
}

static volatile uint32_t zbReportes = 0;  // reportes de temperatura/humedad recibidos (diagnóstico)
static void registrarLectura(esp_zb_zcl_addr_t src, uint8_t endpoint, float valor, bool esTemp) {
  int idx = sensorDeOrigen(src, endpoint);
  if (idx < 0) return;
  zbReportes++;
  float bruto = valor;
  float corr = correccionSensor(sensores[idx].ieee, esTemp);
  valor += corr;  // desde aquí todo (pantalla, alarmas, CSV) usa el valor corregido
  portENTER_CRITICAL(&mux);
  Sensor &s = sensores[idx];
  bool primero = !s.reportoTrasArranque;
  s.reportoTrasArranque = true;
  if (esTemp) {
    s.temp = valor;
    s.tieneTemp = true;
  } else {
    s.hum = valor;
    s.tieneHum = true;
  }
  s.ultimoMs = millis();
  s.despierto = true;
  portEXIT_CRITICAL(&mux);
  if (primero) {
    // Mide cuánto tarda cada sensor en volver tras un reinicio del monitor.
    char nombre[32];
    nombreSensor(idx, sensores[idx].ieee, nombre, sizeof(nombre));
    registrarEvento("SENSOR_PRIMER_REPORTE", "%s: a los %lu min del arranque", nombre, (unsigned long)(millis() / 60000));
  }
  evaluarAlarma(idx, esTemp);

  if (corr != 0)
    Serial.printf("[S%d] %s = %.2f%s (sensor %.2f, correccion %+.1f)\n", idx + 1, esTemp ? "Temp" : "Hum", valor,
                  esTemp ? " C" : " %", bruto, corr);
  else
    Serial.printf("[S%d] %s = %.2f%s\n", idx + 1, esTemp ? "Temp" : "Hum", valor, esTemp ? " C" : " %");
}

static void registrarBateria(esp_zb_zcl_addr_t src, uint8_t endpoint, int pct, bool porVoltaje) {
  int idx = sensorDeOrigen(src, endpoint);
  if (idx < 0) return;
  const uint32_t ventanaMs = (uint32_t)BATERIA_VENTANA_H * 3600000UL;
  bool usado = true;
  portENTER_CRITICAL(&mux);
  Sensor &s = sensores[idx];
  uint32_t ahora = millis();
  // El porcentaje informado por el sensor tiene prioridad sobre la estimación por voltaje.
  if (porVoltaje && s.tieneBat && !s.batPorVoltaje) {
    usado = false;
  } else {
    // Empieza de cero la primera vez, o al pasar de estimación por voltaje a porcentaje real.
    // También al llegar la primera lectura real después de un reinicio.
    bool reiniciar = !s.tieneBat || s.batGuardada || (s.batPorVoltaje && !porVoltaje);
    uint8_t antes = s.tieneBat ? s.bat : 0xFF;
    s.batGuardada = false;
    if (reiniciar) {
      s.batPico = s.batPicoAnterior = pct;
      s.batVentanaMs = ahora;
    } else if (ahora - s.batVentanaMs > ventanaMs) {
      s.batPicoAnterior = s.batPico;
      s.batPico = pct;
      s.batVentanaMs = ahora;
    } else if (pct > s.batPico) {
      s.batPico = pct;
    }
    s.bat = max(s.batPico, s.batPicoAnterior);
    s.batPorVoltaje = porVoltaje;
    s.tieneBat = true;
    s.batMs = ahora;
    if (s.bat != antes) bateriaCambio = true;
  }
  uint8_t mostrado = s.bat;
  portEXIT_CRITICAL(&mux);

  if (usado) {
    Serial.printf("[S%d] Bateria = %d%%%s (en pantalla %u%%)\n", idx + 1, pct, porVoltaje ? " por voltaje" : "", mostrado);
  }
}

// Sincroniza con la lista de dispositivos enlazados (incluye los recuperados al reiniciar).
static void sincronizarEnlazados() {
  std::list<zb_device_params_t *> lista = zbCoordinador.getBoundDevices();
  for (const auto *d : lista) {
    static const uint8_t cero[8] = {0};
    if (memcmp(d->ieee_addr, cero, 8) == 0) continue;
    indiceSensor(d->ieee_addr, d->short_addr, d->endpoint);
  }
}

// ---- Pedidos a los sensores ----
// Los sensores duermen; los pedidos se envían justo después de que reportan, que es
// cuando están atentos. Se llaman desde loop(), por eso toman el lock de Zigbee.
// Nota: las funciones *_cmd_req devuelven el número de secuencia, no un error.

static void leerAtributos(const Sensor &s, uint8_t epOrigen, uint16_t cluster, uint16_t *attrs, uint8_t n) {
  esp_zb_zcl_read_attr_cmd_t req;
  memset(&req, 0, sizeof(req));
  req.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
  req.zcl_basic_cmd.dst_addr_u.addr_short = s.shortAddr;
  req.zcl_basic_cmd.dst_endpoint = s.endpoint;
  req.zcl_basic_cmd.src_endpoint = epOrigen;
  req.clusterID = cluster;
  req.attr_number = n;
  req.attr_field = attrs;
  esp_zb_lock_acquire(portMAX_DELAY);
  esp_zb_zcl_read_attr_cmd_req(&req);
  esp_zb_lock_release();
}

static void configurarReporte(const Sensor &s, uint8_t epOrigen, uint16_t cluster, uint16_t attr, uint8_t tipo,
                              uint16_t minS, uint16_t maxS, void *cambio) {
  esp_zb_zcl_config_report_record_t rec = {
    .direction = ESP_ZB_ZCL_REPORT_DIRECTION_SEND,
    .attributeID = attr,
    .attrType = tipo,
    .min_interval = minS,
    .max_interval = maxS,
    .reportable_change = cambio,
  };
  esp_zb_zcl_config_report_cmd_t cmd;
  memset(&cmd, 0, sizeof(cmd));
  cmd.address_mode = ESP_ZB_APS_ADDR_MODE_16_ENDP_PRESENT;
  cmd.zcl_basic_cmd.dst_addr_u.addr_short = s.shortAddr;
  cmd.zcl_basic_cmd.dst_endpoint = s.endpoint;
  cmd.zcl_basic_cmd.src_endpoint = epOrigen;
  cmd.clusterID = cluster;
  cmd.record_number = 1;
  cmd.record_field = &rec;
  esp_zb_lock_acquire(portMAX_DELAY);
  esp_zb_zcl_config_report_cmd_req(&cmd);
  esp_zb_lock_release();
}

static void alEnlazarBateria(esp_zb_zdp_status_t estado, void *ctx) {
  if (estado == ESP_ZB_ZDP_STATUS_SUCCESS) Serial.println("Enlace de bateria confirmado");
  else Serial.printf("Enlace de bateria fallo (estado %d)\n", estado);
}

// Pide al sensor que envíe su batería al endpoint de batería de este coordinador.
static void enlazarBateria(const Sensor &s) {
  esp_zb_zdo_bind_req_param_t req;
  memset(&req, 0, sizeof(req));
  req.req_dst_addr = s.shortAddr;
  memcpy(req.src_address, s.ieee, 8);
  req.src_endp = s.endpoint;
  req.cluster_id = ESP_ZB_ZCL_CLUSTER_ID_POWER_CONFIG;
  req.dst_addr_mode = ESP_ZB_ZDO_BIND_DST_ADDR_MODE_64_BIT_EXTENDED;
  req.dst_endp = zbCoordinador.getEndpoint();
  esp_zb_lock_acquire(portMAX_DELAY);
  esp_zb_get_long_address(req.dst_address_u.addr_long);
  esp_zb_zdo_device_bind_req(&req, alEnlazarBateria, nullptr);
  esp_zb_lock_release();
}

static void atenderSensores() {
  const uint32_t leerBatCadaMs = (uint32_t)LEER_BATERIA_CADA_H * 3600000UL;
  for (int i = 0; i < MAX_SENSORES; i++) {
    Sensor s;
    portENTER_CRITICAL(&mux);
    s = sensores[i];
    bool listo = s.usado && s.despierto && s.endpoint != 0 && s.shortAddr != 0xFFFF;
    if (listo) {
      sensores[i].despierto = false;
      sensores[i].identificar = false;
      sensores[i].configurado = true;
    }
    portEXIT_CRITICAL(&mux);
    if (!listo) continue;

    if (s.identificar) {
      // La respuesta la imprime la librería: "Peer Manufacturer is ..." / "Peer Model is ..."
      uint16_t attrs[] = {ESP_ZB_ZCL_ATTR_BASIC_MANUFACTURER_NAME_ID, ESP_ZB_ZCL_ATTR_BASIC_MODEL_IDENTIFIER_ID};
      leerAtributos(s, zbCoordinador.getEndpoint(), ESP_ZB_ZCL_CLUSTER_ID_BASIC, attrs, 2);
    }

    if (!s.configurado) {
      enlazarBateria(s);
      if (CONFIGURAR_REPORTES) {
        int16_t dTemp = (int16_t)(REPORTE_DELTA_TEMP * 100);
        uint16_t dHum = (uint16_t)(REPORTE_DELTA_HUM * 100);
        uint8_t dBat = 2;  // 1 %
        configurarReporte(s, zbCoordinador.getEndpoint(), ESP_ZB_ZCL_CLUSTER_ID_TEMP_MEASUREMENT, ESP_ZB_ZCL_ATTR_TEMP_MEASUREMENT_VALUE_ID,
                          ESP_ZB_ZCL_ATTR_TYPE_S16, REPORTE_MIN_S, REPORTE_MAX_S, &dTemp);
        configurarReporte(s, zbCoordinador.getEndpoint(), ESP_ZB_ZCL_CLUSTER_ID_REL_HUMIDITY_MEASUREMENT,
                          ESP_ZB_ZCL_ATTR_REL_HUMIDITY_MEASUREMENT_VALUE_ID, ESP_ZB_ZCL_ATTR_TYPE_U16, REPORTE_MIN_S, REPORTE_MAX_S, &dHum);
        configurarReporte(s, zbCoordinador.getEndpoint(), ESP_ZB_ZCL_CLUSTER_ID_POWER_CONFIG, ATTR_BATERIA_PCT,
                          ESP_ZB_ZCL_ATTR_TYPE_U8, REPORTE_BAT_MIN_S, REPORTE_BAT_MAX_S, &dBat);
      }
      Serial.printf("[S%d] Enlace de bateria y reportes enviados\n", i + 1);
    }

    // Sin un valor real del sensor (o solo el guardado en memoria), se pide en cada
    // reporte; con valor real, como máximo cada 10 min.
    bool sinValorReal = !s.tieneBat || s.batGuardada;
    bool batVieja = sinValorReal || millis() - s.batMs > leerBatCadaMs;
    uint32_t espera = sinValorReal ? 30000UL : 600000UL;
    bool pedidoReciente = s.ultimoPedidoBatMs != 0 && millis() - s.ultimoPedidoBatMs < espera;
    if (batVieja && !pedidoReciente) {
      uint16_t attrs[] = {ATTR_BATERIA_PCT, ATTR_BATERIA_VOLT};
      leerAtributos(s, zbCoordinador.getEndpoint(), ESP_ZB_ZCL_CLUSTER_ID_POWER_CONFIG, attrs, 2);
      portENTER_CRITICAL(&mux);
      sensores[i].ultimoPedidoBatMs = millis();
      portEXIT_CRITICAL(&mux);
    }
  }
}

// ======================= Persistencia =======================
// Se guarda el orden de los sensores (para que conserven su número al reiniciar)
// y el último % de batería mostrado de cada uno (0xFF = desconocido).

static void guardarLista() {
  uint8_t buf[MAX_SENSORES * 8];
  uint8_t bat[MAX_SENSORES];
  uint8_t n = 0;
  portENTER_CRITICAL(&mux);
  for (int i = 0; i < MAX_SENSORES; i++) {
    if (!sensores[i].usado) continue;
    bat[n] = sensores[i].tieneBat ? sensores[i].bat : 0xFF;
    memcpy(&buf[8 * n++], sensores[i].ieee, 8);
  }
  portEXIT_CRITICAL(&mux);
  prefs.putUChar("n", n);
  prefs.putBytes("ieee", buf, 8 * n);
  prefs.putBytes("bat", bat, n);
}

static void cargarLista() {
  uint8_t n = prefs.getUChar("n", 0);
  if (n > MAX_SENSORES) n = MAX_SENSORES;
  uint8_t buf[MAX_SENSORES * 8];
  if (n == 0 || prefs.getBytes("ieee", buf, 8 * n) != 8 * n) return;
  uint8_t bat[MAX_SENSORES];
  bool hayBat = prefs.getBytes("bat", bat, n) == n;
  for (int i = 0; i < n; i++) {
    Sensor &s = sensores[i];
    if (sensorOculto(&buf[8 * i])) continue;  // fuera de servicio: su espacio queda libre
    s.usado = true;
    s.shortAddr = 0xFFFF;
    memcpy(s.ieee, &buf[8 * i], 8);
    if (hayBat && bat[i] <= 100) {
      s.tieneBat = true;
      s.batGuardada = true;
      s.bat = s.batPico = s.batPicoAnterior = bat[i];
      s.batVentanaMs = millis();
    }
  }
  Serial.printf("%u sensores cargados de memoria\n", n);
}

// ======================= Pantalla =======================

// Colores de las directrices de diseño de Fricke Store (modo oscuro de frontend/css/base.css del
// portal), pasados a RGB565. Ningún color se escribe fuera de esta lista. Los estados siempre van
// con texto (En rango / ALARMA / ! aviso), nunca solo con el color.
#define C_FONDO    0x10C4  // --fondo          #141A22
#define C_CABECERA 0x1926  // --superficie     #1D2530 (cabecera y barra inferior)
#define C_EMPAREJA 0x120D  // --primario-suave #17406F (emparejando)
#define C_TEXTO    0xE77E  // --texto          #E6ECF3
#define C_TENUE    0x8CD4  // --texto-3        #8D98A5
#define C_CLARO    0xC67A  // --texto-2        #C3CCD6
#define C_LINEA    0x2187  // --borde-suave    #26313D
#define C_NORMAL   0x8652  // --ok             #81C995 (en rango)
#define C_FRIO     0x85BE  // --primario       #82B4F5
#define C_CALOR    0xF5D6  // --peligro        #F2B8B5 (fuera de rango, en texto)
#define C_AVISO    0xFD88  // naranja Hospital #FCB040 (atención)
#define C_AVISO_FONDO 0x120D   // --primario-suave: cabecera con un mensaje
#define C_ALARMA_FONDO 0xC145  // --peligro (modo claro) #C62828: fila y cabecera en alarma
#define C_ALARMA_VIVO  0xC145  // --peligro (modo claro) #C62828: valor fuera de rango y vista de alarma
#define C_ALARMA_OSCURO 0x10C4 // --fondo: la vista de alarma parpadea entre rojo y fondo

// Bus SPI de Arduino compartido con la micro SD (el C6 tiene un solo SPI de uso general).
// La pantalla debe iniciarse antes que la SD: es la que fija los pines del bus.
Arduino_DataBus *bus = new Arduino_HWSPI(TFT_DC, TFT_CS, TFT_SCK, TFT_MOSI, SD_MISO, &SPI, true);
// La pantalla depende de la configuración del equipo: se crea en setup().
Arduino_GFX *panel = nullptr;
// Canvas de 8 bits por píxel (paleta de hasta 256 colores): usa la mitad de RAM que uno de
// 16 bits (75 KB en vez de 150 KB con la pantalla de 2,4") y deja memoria para el WiFi.
Arduino_Canvas_Indexed *gfx = nullptr;
static int ultimoDesplazamiento = -1;
static int ANCHO = 170;
static const int ALTO = 320;

static void crearPantalla() {
  if (cfg.pantalla == 2) {
    // 2,4" 240x320: el controlador ST7789V cubre 240 columnas, sin desplazamiento.
    ANCHO = 240;
    panel = new Arduino_ST7789(bus, TFT_RST, 0, true, 240, 320, 0, 0, 0, 0);
  } else {
    // 1,9" 170x320: el panel ocupa las columnas 35 a 204 del controlador.
    ANCHO = 170;
    panel = new Arduino_ST7789(bus, TFT_RST, 0, true, 170, 320, 35, 0, 35, 0);
  }
  gfx = new Arduino_Canvas_Indexed(ANCHO, ALTO, panel);
}
static const int ALTO_CABECERA = 42;  // hora y fecha, avisos, SD y página
static const int ALTO_BARRA = 16;     // barra inferior: emparejamiento y estado
static const int ALTO_FILA = (ALTO - ALTO_CABECERA - ALTO_BARRA) / FILAS_POR_PAGINA;

static uint32_t emparejarHastaMs = 0;
static int pagina = 0;
static uint32_t ultimoCambioPagina = 0;
static uint32_t brilloAltoHastaMs = 0;  // hasta cuándo dura el brillo alto por botón

// Marca actividad del usuario: la pantalla sube al brillo alto por BRILLO_ACTIVO_S.
static void pantallaActiva() {
  brilloAltoHastaMs = millis() + BRILLO_ACTIVO_S * 1000UL;
}

// Decide si ahora corresponde mostrar el logo: LOGO_SEGUNDOS cada LOGO_CADA_MIN.
// Si está bloqueado (alarma, aviso...) se corta o se posterga hasta que se pueda.
static volatile bool logoAhora = false;  // comando serie LOGO: mostrarlo ya (para probar)

static bool logoActivo(bool bloqueado) {
  static uint32_t proximoMs = LOGO_CADA_MIN * 60000UL;
  static uint32_t hastaMs = 0;
  static bool mostrando = false;
  if (logoAhora && !mostrando) {
    logoAhora = false;
    proximoMs = millis();
  }
  if (mostrando) {
    if (!bloqueado && (int32_t)(hastaMs - millis()) > 0) return true;
    mostrando = false;
    proximoMs = millis() + LOGO_CADA_MIN * 60000UL;
    return false;
  }
  if (bloqueado || (int32_t)(millis() - proximoMs) < 0) return false;
  mostrando = true;
  hastaMs = millis() + LOGO_SEGUNDOS * 1000UL;
  return true;
}

// ======================= Hora =======================

static bool horaValida() {
  return time(nullptr) > 1735689600;  // posterior a 2025-01-01
}

// ======================= Reloj RTC DS3231 =======================
// Se guarda en UTC; la zona horaria la aplica el sistema al mostrar.

static const uint8_t RTC_DIR = 0x68;
static bool rtcOk = false;
static bool rtcFalla = false;  // el DS3231 dejó de responder (o no estaba al arrancar)

// ¿Responde el DS3231 en el bus I2C? Si antes falló, reinicia el bus: tras
// desconectar un cable con el bus activo, el controlador I2C queda en error y
// no vuelve a comunicarse aunque el reloj ya esté conectado.
static bool rtcResponde() {
  if (rtcFalla || !rtcOk) {
    Wire.end();
    Wire.begin(RTC_SDA, RTC_SCL);
  }
  Wire.beginTransmission(RTC_DIR);
  return Wire.endTransmission() == 0;
}

static uint8_t aBcd(int v) { return ((v / 10) << 4) | (v % 10); }
static int deBcd(uint8_t v) { return (v >> 4) * 10 + (v & 0x0F); }

static bool iniciarRTC() {
  Wire.begin(RTC_SDA, RTC_SCL);
  Wire.beginTransmission(RTC_DIR);
  rtcOk = Wire.endTransmission() == 0;
  Serial.println(rtcOk ? "Reloj RTC detectado" : "Reloj RTC no detectado");
  return rtcOk;
}

// Devuelve 0 si no hay reloj o su hora no es válida (p. ej. sin pila y sin configurar).
static time_t leerRTC() {
  if (!rtcOk) return 0;
  Wire.beginTransmission(RTC_DIR);
  Wire.write(0x00);
  if (Wire.endTransmission() != 0 || Wire.requestFrom(RTC_DIR, (uint8_t)7) != 7) return 0;
  uint8_t r[7];
  for (int i = 0; i < 7; i++) r[i] = Wire.read();
  int seg = deBcd(r[0] & 0x7F), min = deBcd(r[1] & 0x7F), hora = deBcd(r[2] & 0x3F);
  int dia = deBcd(r[4] & 0x3F), mes = deBcd(r[5] & 0x1F), anio = 2000 + deBcd(r[6]);
  if (mes < 1 || mes > 12 || dia < 1 || dia > 31) return 0;
  // Días desde 1970-01-01 (algoritmo "days from civil" de H. Hinnant).
  int y = anio - (mes <= 2);
  long era = y / 400;
  long yoe = y - era * 400;
  long doy = (153L * (mes + (mes > 2 ? -3 : 9)) + 2) / 5 + dia - 1;
  long doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
  long dias = era * 146097 + doe - 719468;
  time_t utc = (time_t)dias * 86400 + hora * 3600 + min * 60 + seg;
  return utc > 1735689600 ? utc : 0;
}

static void escribirRTC(time_t utc) {
  if (!rtcOk) return;
  struct tm t;
  gmtime_r(&utc, &t);
  Wire.beginTransmission(RTC_DIR);
  Wire.write(0x00);
  Wire.write(aBcd(t.tm_sec));
  Wire.write(aBcd(t.tm_min));
  Wire.write(aBcd(t.tm_hour));  // formato 24 h
  Wire.write(aBcd(t.tm_wday + 1));
  Wire.write(aBcd(t.tm_mday));
  Wire.write(aBcd(t.tm_mon + 1));
  Wire.write(aBcd(t.tm_year - 100));
  Wire.endTransmission();
  // DS3231: limpiar el aviso de "oscilador detenido" (bit OSF del registro de estado).
  Wire.beginTransmission(RTC_DIR);
  Wire.write(0x0F);
  Wire.write(0x00);
  Wire.endTransmission();
}

static void fijarHoraSistema(time_t utc) {
  struct timeval tv = {.tv_sec = utc, .tv_usec = 0};
  settimeofday(&tv, nullptr);
}

// El reloj interno del C6 se desvía (varios minutos por día): se corrige con el
// DS3231 cada SINCRONIZAR_RTC_MIN.
// Cada SINCRONIZAR_RTC_MIN corrige la hora con el DS3231. Si el reloj no
// responde (se soltó o no estaba al arrancar) lo registra y lo sigue buscando cada
// minuto: al volver, toma su hora y el registro en la SD se retoma solo.
static void sincronizarConRTC() {
  static uint32_t ultimaMs = 0;
  bool urgente = rtcFalla || !horaValida();
  uint32_t cada = urgente ? 60000UL : (uint32_t)SINCRONIZAR_RTC_MIN * 60000UL;
  if (millis() - ultimaMs < cada) return;
  ultimaMs = millis();
  rtcOk = rtcResponde();
  time_t rtc = leerRTC();
  if (!rtc) {
    if (!rtcFalla) {
      rtcFalla = true;
      registrarEvento("RTC_AUSENTE", rtcOk ? "el DS3231 no tiene hora valida" : "el reloj DS3231 no responde; %s",
                      horaValida() ? "se sigue con el reloj interno" : "sin hora no se graba en la SD");
    }
    return;
  }
  bool estabaSinHora = !horaValida();
  long deriva = estabaSinHora ? 0 : (long)(time(nullptr) - rtc);
  fijarHoraSistema(rtc);
  if (rtcFalla) {
    rtcFalla = false;
    registrarEvento("RTC_RECUPERADO", estabaSinHora ? "hora tomada del DS3231; se retoma el registro"
                                                    : "el reloj interno iba %+ld s respecto del DS3231", deriva);
  } else if (labs(deriva) >= HORA_DERIVA_EVENTO_S) {
    registrarEvento("HORA_CORREGIDA", "el reloj interno iba %+ld s respecto del DS3231", deriva);
  }
}

// Pone en hora desde el PC (segundos unix UTC). Devuelve false si el valor no es válido.
static bool fijarHoraUSB(time_t utc) {
  if (utc <= 1735689600) return false;
  char antes[20];
  fechaActual(antes);
  long diferencia = horaValida() ? (long)(utc - time(nullptr)) : 0;
  fijarHoraSistema(utc);
  escribirRTC(utc);
  char txt[24];
  struct tm t;
  localtime_r(&utc, &t);
  strftime(txt, sizeof(txt), "%Y-%m-%d %H:%M:%S", &t);
  Serial.printf("Hora fijada: %s%s\n", txt, rtcOk ? " (guardada en el RTC)" : " (sin RTC: se pierde al reiniciar)");
  registrarEvento("HORA_AJUSTADA", "de %s a %s (%+ld s) por USB", antes, txt, diferencia);
  return true;
}

// Agrega a s un texto JSON entre comillas (los textos de la configuración ya vienen
// limpios de comillas; por si acaso se escapan).
static void jsonTexto(String &s, const char *txt) {
  s += '"';
  for (; *txt; txt++) {
    if (*txt == '"' || *txt == '\\') s += '\\';
    s += *txt;
  }
  s += '"';
}

// Comandos por el monitor serie: los del Configurador (@...) y los de diagnóstico
// para una persona (HORA <segundos unix UTC>, EQUIPO, ESTADO, VECINOS, RTC...).
// ================================ WiFi: envío de lecturas ================================
// Opcional (desde la 2.1). Red, clave y servidor se guardan en la NVS (espacio "wifi") con
// el Configurador (@WIFI_SET). Cada WIFI_ENVIO_S envía las lecturas por HTTP POST (JSON) al
// servidor. Lo local (pantalla, alarmas, SD firmada) no depende del WiFi. La radio se
// comparte con Zigbee (coexistencia de Espressif, esp_coex_wifi_i154_enable).
static const uint32_t WIFI_ENVIO_S = 60;
static const uint32_t WIFI_MEMORIA_MINIMA = 70000;  // bytes libres para encender el WiFi
static volatile bool wifiActivo = false;
static bool wifiIniciado = false;
static volatile uint32_t wifiOk = 0, wifiFallas = 0;
static void serieEquipo(char *out);
static char wifiRed[33] = "";
static char wifiServidor[101] = "";
static portMUX_TYPE muxWifi = portMUX_INITIALIZER_UNLOCKED;

static void wifiApagar(const char *motivo) {
  bool estaba = wifiActivo;
  wifiActivo = false;
  if (wifiIniciado) {
    WiFi.disconnect(true);
    WiFi.mode(WIFI_OFF);
    wifiIniciado = false;
  }
  if (estaba || motivo[0]) {
    Serial.printf("[WiFi] apagado %s\n", motivo);
    registrarEvento("WIFI_APAGADO", "%s", motivo[0] ? motivo : "por configuracion");
  }
}

// Copia la dirección del servidor sin la credencial: "http://equipo:clave@host/..." queda
// "http://****@host/...". Es lo que se escribe por el puerto serie y en el registro de eventos
// (que va a la SD y al portal): la clave del equipo nunca queda a la vista (firmware 2.5).
static void servidorSinClave(const char *url, char *out, size_t len) {
  const char *esquema = strstr(url, "://");
  const char *arroba = strchr(url, '@');
  if (!esquema || !arroba || arroba < esquema) {
    strlcpy(out, url, len);
    return;
  }
  snprintf(out, len, "%.*s****%s", (int)(esquema + 3 - url), url, arroba);
}

// Lee la configuración y enciende (o apaga) el WiFi. alArrancar: no lo enciende si el
// reinicio anterior fue por una falla, para no quedar en un ciclo de reinicios.
static void wifiAplicar(bool alArrancar) {
  Preferences p;
  String red, clave, servidor;
  if (p.begin("wifi", true)) {
    red = p.getString("red", "");
    clave = p.getString("clave", "");
    servidor = p.getString("servidor", "");
    p.end();
  }
  portENTER_CRITICAL(&muxWifi);
  strlcpy(wifiRed, red.c_str(), sizeof(wifiRed));
  strlcpy(wifiServidor, servidor.c_str(), sizeof(wifiServidor));
  portEXIT_CRITICAL(&muxWifi);
  if (!red.length()) {
    wifiApagar("");
    return;
  }
  esp_reset_reason_t rr = esp_reset_reason();
  if (alArrancar && (rr == ESP_RST_PANIC || rr == ESP_RST_INT_WDT || rr == ESP_RST_TASK_WDT || rr == ESP_RST_WDT)) {
    wifiApagar("hasta configurarlo de nuevo: el reinicio anterior fue por una falla");
    return;
  }
  uint32_t libre = ESP.getFreeHeap();
  if (libre < WIFI_MEMORIA_MINIMA) {
    char m[64];
    snprintf(m, sizeof m, "por poca memoria libre (%lu bytes)", (unsigned long)libre);
    wifiApagar(m);
    return;
  }
  if (wifiIniciado) WiFi.disconnect(true);
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(red.c_str(), clave.c_str());
  esp_err_t e = esp_coex_wifi_i154_enable();
  wifiIniciado = true;
  wifiActivo = true;
  char visible[sizeof(wifiServidor)];
  servidorSinClave(servidor.c_str(), visible, sizeof(visible));
  Serial.printf("[WiFi] conectando a %s; servidor %s; memoria libre %lu; coexistencia %s\n", red.c_str(),
                servidor.length() ? visible : "(ninguno)", (unsigned long)libre, esp_err_to_name(e));
  registrarEvento("WIFI_ENCENDIDO", "red %s, servidor %s", red.c_str(), servidor.length() ? visible : "ninguno");
}

// Estado de la SD para el envío WiFi (firmware 2.2). Lo actualiza revisarAlertaSD() en el loop y lo lee la tarea
// del WiFi: así el portal avisa que la SD no graba sin esperar a que alguien la importe (variables de 32 bits:
// se leen y escriben de una vez en el ESP32, sin candado).
static volatile uint32_t envioSdOk = 1;          // 1 = la SD está grabando; 0 = no (falta, falla o se retiró)
static volatile uint32_t envioSdFueraS = 0;      // segundos que lleva sin grabar
static volatile uint32_t envioPendientes = 0;    // filas firmadas esperando en la flash

static void tareaWiFi(void *) {
  uint32_t seq = 0;
  for (;;) {
    vTaskDelay(pdMS_TO_TICKS(WIFI_ENVIO_S * 1000));
    char servidor[sizeof(wifiServidor)];
    portENTER_CRITICAL(&muxWifi);
    strlcpy(servidor, wifiServidor, sizeof(servidor));
    portEXIT_CRITICAL(&muxWifi);
    if (!wifiActivo || !servidor[0]) continue;
    if (WiFi.status() != WL_CONNECTED) {
      wifiFallas++;
      continue;
    }
    char serie[17];
    serieEquipo(serie);
    String j;
    j.reserve(1500);
    j += "{\"monitor\":";
    jsonTexto(j, cfg.codigo);
    j += ",\"serie\":\"";
    j += serie;
    j += "\",\"firmware\":\"" VERSION_FIRMWARE "\",\"seq\":";
    j += ++seq;
    j += ",\"unix\":";
    j += (long)(horaValida() ? time(nullptr) : 0);
    j += ",\"uptime_s\":";
    j += millis() / 1000;
    j += ",\"rssi\":";
    j += WiFi.RSSI();
    j += ",\"heap\":";
    j += ESP.getFreeHeap();
    j += ",\"zb_reportes\":";
    j += zbReportes;
    j += ",\"envios_ok\":";
    j += wifiOk;
    j += ",\"envios_falla\":";
    j += wifiFallas;
    j += ",\"sd\":";
    j += (unsigned long)envioSdOk;
    j += ",\"sd_fuera_s\":";
    j += (unsigned long)envioSdFueraS;
    j += ",\"pendientes\":";
    j += (unsigned long)envioPendientes;
    j += ",\"sensores\":[";
    bool primero = true;
    for (int i = 0; i < MAX_SENSORES; i++) {
      portENTER_CRITICAL(&mux);
      Sensor s = sensores[i];
      portEXIT_CRITICAL(&mux);
      if (!s.usado) continue;
      char nombre[32], ieee[17];
      nombreSensor(i, s.ieee, nombre, sizeof(nombre));
      ieeeATexto(s.ieee, ieee);
      j += primero ? "{\"n\":" : ",{\"n\":";
      primero = false;
      j += i + 1;
      j += ",\"ieee\":\"";
      j += ieee;
      j += "\",\"nombre\":";
      jsonTexto(j, nombre);
      j += ",\"temp\":";
      j += s.tieneTemp ? String(s.temp, 1) : String("null");
      j += ",\"hum\":";
      j += s.tieneHum ? String(s.hum, 0) : String("null");
      j += ",\"edad_s\":";
      j += s.ultimoMs ? (millis() - s.ultimoMs) / 1000 : 0;
      j += ",\"bat\":";
      j += s.tieneBat ? (int)s.bat : -1;
      j += ",\"alarma_t\":";
      j += s.enAlarma ? 1 : 0;
      j += ",\"alarma_h\":";
      j += s.enAlarmaHum ? 1 : 0;
      j += "}";
    }
    j += "]}";
    HTTPClient http;
    http.setTimeout(5000);
    http.begin(servidor);
    http.addHeader("Content-Type", "application/json");
    uint32_t t0 = millis();
    int cod = http.POST(j);
    http.end();
    if (cod >= 200 && cod < 300) wifiOk++;
    else wifiFallas++;
    Serial.printf("[WiFi] envio #%lu: HTTP %d en %lu ms (ok %lu, fallas %lu, rssi %d)\n", (unsigned long)seq, cod,
                  (unsigned long)(millis() - t0), (unsigned long)wifiOk, (unsigned long)wifiFallas, WiFi.RSSI());
  }
}

// Diagnóstico de la convivencia WiFi/Zigbee: cada hora, cuántos reportes de sensores llegaron.
static void estadisticaZigbeeHora() {
  static uint32_t t0 = 0, base = 0;
  static bool habiaWiFi = false;
  if (t0 == 0) {
    t0 = millis() | 1;
    base = zbReportes;
    habiaWiFi = wifiActivo;
    return;
  }
  if (millis() - t0 < 3600000UL) return;
  registrarEvento("ZB_REPORTES_HORA", "%lu reportes en 1 h; WiFi %s; envios ok %lu, fallas %lu",
                  (unsigned long)(zbReportes - base),
                  (habiaWiFi && wifiActivo) ? "encendido" : (habiaWiFi || wifiActivo) ? "cambio" : "apagado",
                  (unsigned long)wifiOk, (unsigned long)wifiFallas);
  t0 = millis() | 1;
  base = zbReportes;
  habiaWiFi = wifiActivo;
}

static void wifiEstadoJson(String &s) {
  s += "@WIFI {\"configurado\":";
  s += wifiRed[0] ? 1 : 0;
  s += ",\"red\":";
  jsonTexto(s, wifiRed);
  s += ",\"servidor\":";
  jsonTexto(s, wifiServidor);
  s += ",\"activo\":";
  s += wifiActivo ? 1 : 0;
  bool con = wifiIniciado && WiFi.status() == WL_CONNECTED;
  s += ",\"conectado\":";
  s += con ? 1 : 0;
  s += ",\"ip\":\"";
  s += con ? WiFi.localIP().toString() : String("");
  s += "\",\"rssi\":";
  s += con ? WiFi.RSSI() : 0;
  s += ",\"envios_ok\":";
  s += wifiOk;
  s += ",\"envios_falla\":";
  s += wifiFallas;
  s += ",\"memoria_libre\":";
  s += ESP.getFreeHeap();
  s += "}";
}

// Comandos del Configurador para el WiFi. Devuelve true si el comando era de WiFi.
static bool comandoWiFiConfigurador(const char *linea) {
  if (strcmp(linea, "@WIFI?") == 0) {
    String s;
    wifiEstadoJson(s);
    Serial.println(s);
    return true;
  }
  if (strcmp(linea, "@WIFI_BORRAR") == 0) {
    Preferences p;
    p.begin("wifi", false);
    p.clear();
    p.end();
    registrarEvento("CONFIG_WIFI", "WiFi desactivado: red, clave y servidor borrados");
    wifiAplicar(false);
    Serial.println("@OK");
    return true;
  }
  if (strncmp(linea, "@WIFI_SET ", 10) == 0) {
    // red|clave|servidor. Clave vacía = conservar la guardada (si la red no cambia).
    char buf[200];
    strlcpy(buf, linea + 10, sizeof(buf));
    char *red = buf, *clave = strchr(red, '|'), *servidor = clave ? strchr(clave + 1, '|') : nullptr;
    if (!clave || !servidor) {
      Serial.println("@ERROR formato: red|clave|servidor");
      return true;
    }
    *clave++ = '\0';
    *servidor++ = '\0';
    if (!red[0] || strlen(red) > 32 || strlen(clave) > 63 || strlen(servidor) > 100 ||
        (servidor[0] && strncmp(servidor, "http://", 7) != 0 && strncmp(servidor, "https://", 8) != 0)) {
      Serial.println("@ERROR red de 1 a 32 caracteres, clave hasta 63, servidor http://... hasta 100");
      return true;
    }
    Preferences p;
    p.begin("wifi", false);
    if (!clave[0]) {
      if (p.getString("red", "") != red) {
        p.end();
        Serial.println("@ERROR escriba la clave de la red nueva");
        return true;
      }
    } else {
      p.putString("clave", clave);
    }
    p.putString("red", red);
    p.putString("servidor", servidor);
    p.end();
    registrarEvento("CONFIG_WIFI", "red %s, servidor %s", red, servidor[0] ? servidor : "ninguno");
    wifiAplicar(false);
    Serial.println("@OK");
    return true;
  }
  return false;
}
// =========================================================================================

static void revisarComandoSerie() {
  static char linea[200];
  static uint8_t largo = 0;
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      linea[largo] = '\0';
      largo = 0;
      if (linea[0] == '@') {
        comandoConfigurador(linea);
      } else if (strcmp(linea, "WIFI?") == 0) {
        String s;
        wifiEstadoJson(s);
        Serial.println(s);
      } else if (strncmp(linea, "HORA ", 5) == 0) {
        if (!fijarHoraUSB((time_t)atoll(linea + 5))) Serial.println("HORA invalida");
      } else if (strcmp(linea, "EQUIPO") == 0) {
        char serie[17];
        serieEquipo(serie);
        Serial.printf("Equipo %s  serie %s  firmware %s  pantalla %dx%d\n", cfg.codigo, serie, VERSION_FIRMWARE,
                      ANCHO, ALTO);
        Serial.printf("Energia: %lu mV en GPIO %d, deteccion %s, %s\n", (unsigned long)energiaMv, ENERGIA_PIN,
                      energiaArmada ? "activa" : "esperando el divisor", sinRed ? "SIN RED (bateria)" : "con red");
      } else if (strcmp(linea, "ENERGIA OFF") == 0) {
        // Apaga la detección de corte de luz (firmware 2.5): para un equipo sin divisor o al que se
        // le sacó el módulo UPS (si no, con el pin en 0 V avisaría "SIN LUZ" para siempre). Se
        // vuelve a activar sola cuando el pin muestra otra vez el voltaje del divisor.
        energiaArmada = false;
        prefs.putBool("energia", false);
        if (sinRed) {
          sinRed = false;
          alarmaCambio = true;
        }
        registrarEvento("RESPALDO_ENERGIA", "deteccion de corte de luz desactivada por USB");
        Serial.println("Deteccion de corte de luz desactivada (se activa sola al ver el divisor)");
      } else if (strcmp(linea, "LOGO") == 0) {
        logoAhora = true;
        Serial.println("Mostrando el logo");
      } else if (strcmp(linea, "RTC") == 0) {
        bool responde = rtcResponde();
        rtcOk = responde;
        time_t r = leerRTC();
        Serial.printf("RTC: responde=%d hora_valida=%d falla_registrada=%d\n", responde, r != 0, rtcFalla);
      } else if (strcmp(linea, "VECINOS") == 0) {
        static esp_zb_nwk_neighbor_info_t v[MAX_SENSORES + 4];
        int n = leerVecinos(v, MAX_SENSORES + 4);
        Serial.printf("%d vecinos en la tabla de red\n", n);
        for (int i = 0; i < n; i++) {
          int idx = -1;
          for (int j = 0; j < MAX_SENSORES; j++)
            if (sensores[j].usado && memcmp(sensores[j].ieee, v[i].ieee_addr, 8) == 0) idx = j;
          Serial.printf("  0x%04X S%d relacion=%u tipo=%u timeout=%lus contador=%lums lqi=%u rssi=%d\n", v[i].short_addr,
                        idx + 1, v[i].relationship, v[i].device_type, (unsigned long)v[i].device_timeout,
                        (unsigned long)v[i].timeout_counter, v[i].lqi, v[i].rssi);
        }
      } else if (strcmp(linea, "ESTADO") == 0) {
        // Diagnóstico: valores, perfil y alarmas de cada sensor.
        for (int i = 0; i < MAX_SENSORES; i++) {
          Sensor s;
          portENTER_CRITICAL(&mux);
          s = sensores[i];
          portEXIT_CRITICAL(&mux);
          if (!s.usado) continue;
          char nombre[32];
          nombreSensor(i, s.ieee, nombre, sizeof(nombre));
          Serial.printf("S%d %s [%s] T=%.1f%s H=%.0f%s corr=%+.1f/%+.0f edad=%lus alarmaT=%d alarmaH=%d activa=%d\n",
                        i + 1, nombre, perfilSensor(s.ieee).nombre, s.temp, s.tieneTemp ? "" : "(no)", s.hum,
                        s.tieneHum ? "" : "(no)", correccionSensor(s.ieee, true), correccionSensor(s.ieee, false),
                        (unsigned long)((millis() - s.ultimoMs) / 1000), s.enAlarma, s.enAlarmaHum, alarmaActiva(s));
        }
      } else if (strcmp(linea, "BORRAR_RED SI") == 0) {
        borrarRed();
      } else if (strcmp(linea, "BORRAR_RED") == 0) {
        Serial.println("Esto desconecta TODOS los sensores (hay que volver a emparejarlos).");
        Serial.println("Para confirmar, envia: BORRAR_RED SI");
      } else if (strcmp(linea, "CLAVE") == 0) {
        // Clave para verificar las firmas con verificar_registro.py. Quien tenga
        // acceso físico al USB puede leerla: guardarla en un lugar seguro.
        Serial.print("Clave de firma: ");
        for (size_t i = 0; i < sizeof(claveFirma); i++) Serial.printf("%02x", claveFirma[i]);
        Serial.println();
        registrarEvento("CLAVE_LEIDA", "se exporto la clave de firma por USB");
      }
    } else if (largo < sizeof(linea) - 1) {
      linea[largo++] = c;
    }
  }
}

// ======================= Registro (micro SD + flash) =======================
// Dos registros en la SD, un archivo por día cada uno:
//   /datos-AAAA-MM-DD.csv    una fila por sensor cada REGISTRO_CADA_MIN
//   /eventos-AAAA-MM-DD.csv  arranques, alarmas, sensores sin datos, SD, hora...
// Cada fila lleva una firma HMAC-SHA256 (16 hex) encadenada con la fila anterior
// del mismo registro, con una clave secreta de la placa: editar, borrar o insertar
// filas rompe la cadena (se revisa con verificar_registro.py).
// Si la tarjeta no está, las filas ya firmadas se guardan en la flash interna
// (LittleFS) y se pasan a la SD en cuanto vuelve. Sobreviven a un reinicio.

static bool sdOk = false;
static bool flashOk = false;
static uint32_t filasPendientes = 0;
static uint32_t sdFueraDesdeMs = 0;   // desde cuándo la SD no está grabando (0 = está grabando)
static time_t sdFueraDesde = 0;       // lo mismo en hora real (0 si no había hora)

// La SD lleva más de SD_ALERTA_MIN sin grabar (colgada, con falla o retirada).
static bool alertaSDActiva() {
  return !sdOk && sdFueraDesdeMs && millis() - sdFueraDesdeMs >= SD_ALERTA_MIN * 60000UL;
}
static const char *RUTA_PENDIENTES = "/pendientes.csv";
static const char *RUTA_PENDIENTES_TMP = "/pendientes.tmp";
static const char *RUTA_CADENA = "/cadena.txt";   // última firma de cada registro
static const char *RUTA_LATIDO = "/latido.txt";   // última vez que se registró (para detectar huecos)
// Formato del Excel en español: columnas separadas por ';' y decimales con coma.
static const char *ENCABEZADO_DATOS =
  "Fecha y hora;Monitor;Sensor;Nombre;Almacenamiento;IEEE;Temperatura (°C);Humedad (%);Corrección T (°C);Corrección HR (%);"
  "Batería (%);Hora de la lectura;Firma";
static const char *ENCABEZADO_EVENTOS = "Fecha y hora;Monitor;Tipo;Detalle;Firma";

// Monta la SD sin imprimir nada (se usa también para sondear si hay tarjeta).
static bool montarSD() {
  SD.end();
  return SD.begin(SD_CS, SPI, SD_SPI_HZ);
}

static bool iniciarSD() {
  sdOk = montarSD();
  Serial.println(sdOk ? "Micro SD lista" : "Micro SD no detectada");
  return sdOk;
}

// Lee una línea sin el salto final. Devuelve su largo (0 si no quedan).
static size_t leerLinea(File &f, char *buf) {
  size_t n = f.readBytesUntil('\n', buf, LARGO_LINEA - 1);
  if (n > 0 && buf[n - 1] == '\r') n--;
  buf[n] = '\0';
  return n;
}

// ---- Firma ----

static char firmaPrevia[2][17] = {"0000000000000000", "0000000000000000"};  // [0] datos, [1] eventos

static int indiceRegistro(char tipo) {
  return tipo == 'E' ? 1 : 0;
}

// La clave se genera al azar la primera vez y queda en la NVS de la placa.
static void cargarClave() {
  if (prefs.getBytes("clave", claveFirma, sizeof(claveFirma)) == sizeof(claveFirma)) return;
  esp_fill_random(claveFirma, sizeof(claveFirma));
  prefs.putBytes("clave", claveFirma, sizeof(claveFirma));
  Serial.println("Clave de firma nueva generada");
}

static void cargarCadena() {
  if (!flashOk) return;
  File f = LittleFS.open(RUTA_CADENA, "r");
  if (!f) return;
  char linea[LARGO_LINEA];
  for (int i = 0; i < 2 && f.available(); i++) {
    if (leerLinea(f, linea) == 16) snprintf(firmaPrevia[i], sizeof(firmaPrevia[i]), "%s", linea);
  }
  f.close();
}

static void guardarCadena() {
  if (!flashOk) return;
  File f = LittleFS.open(RUTA_CADENA, "w");
  if (!f) return;
  f.printf("%s\n%s\n", firmaPrevia[0], firmaPrevia[1]);
  f.close();
}

// Agrega ",firma" al final de la línea y avanza la cadena de ese registro.
static void firmarLinea(char tipo, char *linea) {
  char *previa = firmaPrevia[indiceRegistro(tipo)];
  uint8_t mac[32];
  mbedtls_md_context_t ctx;
  mbedtls_md_init(&ctx);
  mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 1);
  mbedtls_md_hmac_starts(&ctx, claveFirma, sizeof(claveFirma));
  mbedtls_md_hmac_update(&ctx, (const uint8_t *)previa, 16);
  mbedtls_md_hmac_update(&ctx, (const uint8_t *)linea, strlen(linea));
  mbedtls_md_hmac_finish(&ctx, mac);
  mbedtls_md_free(&ctx);
  for (int i = 0; i < 8; i++) sprintf(previa + 2 * i, "%02x", mac[i]);
  size_t n = strlen(linea);
  snprintf(linea + n, LARGO_LINEA - n, ";%s", previa);
}

// ---- Tarjeta y flash ----

static void iniciarFlash() {
  // La primera vez formatea la partición (tarda unos segundos).
  flashOk = LittleFS.begin(true, "/littlefs", 4, "spiffs");
  if (!flashOk) {
    Serial.println("No se pudo montar la flash interna: sin respaldo si falta la SD");
    return;
  }
  File f = LittleFS.open(RUTA_PENDIENTES, "r");
  if (f) {
    char linea[LARGO_LINEA];
    while (f.available()) {
      if (leerLinea(f, linea) > 0) filasPendientes++;
      alimentarWDT();
    }
    f.close();
  }
  if (filasPendientes) Serial.printf("%lu filas pendientes de pasar a la SD\n", (unsigned long)filasPendientes);
}

// Abre el CSV del día de ese registro (según la fecha al inicio de la línea):
// /datos/AAAA-MM-DD.csv o /eventos/AAAA-MM-DD.csv. Los archivos nuevos empiezan
// con la marca UTF-8 (BOM) para que Excel muestre bien las tildes.
// Si el archivo del día ya existe con otras columnas (cambió el formato durante el
// día), se sigue en AAAA-MM-DD_2.csv, _3... para no mezclar formatos en un archivo.
static bool abrirCsv(char tipo, const char *linea, CsvAbierto &c) {
  const char *carpeta = tipo == 'E' ? "/eventos" : "/datos";
  const char *encabezado = tipo == 'E' ? ENCABEZADO_EVENTOS : ENCABEZADO_DATOS;
  if (!SD.exists(carpeta)) SD.mkdir(carpeta);

  bool nuevo = true;
  for (int k = 1; k <= 9; k++) {
    if (k == 1) snprintf(c.ruta, sizeof(c.ruta), "%s/%.10s.csv", carpeta, linea);
    else snprintf(c.ruta, sizeof(c.ruta), "%s/%.10s_%d.csv", carpeta, linea, k);
    if (!SD.exists(c.ruta)) break;
    File r = SD.open(c.ruta, FILE_READ);
    char primera[LARGO_LINEA];
    size_t n = r ? leerLinea(r, primera) : 0;
    if (r) r.close();
    const char *leida = (n >= 3 && strncmp(primera, "\xEF\xBB\xBF", 3) == 0) ? primera + 3 : primera;
    if (strcmp(leida, encabezado) == 0) {
      nuevo = false;
      break;
    }
  }

  c.f = SD.open(c.ruta, FILE_APPEND);
  if (!c.f) return false;
  c.esperado = c.f.size();
  if (nuevo) {
    size_t n = c.f.printf("\xEF\xBB\xBF%s\n", encabezado);
    c.esperado += n;
  }
  return true;
}

static bool escribirCsv(CsvAbierto &c, const char *linea) {
  size_t n = c.f.printf("%s\n", linea);
  c.esperado += n;
  return n == strlen(linea) + 1;
}

// Cierra el archivo y lo vuelve a abrir para leer su tamaño real: con mal contacto
// la SD puede aceptar la escritura sin que los datos queden guardados.
static bool cerrarVerificando(CsvAbierto &c) {
  c.f.close();
  File g = SD.open(c.ruta, FILE_READ);
  size_t real = g ? g.size() : 0;
  if (g) g.close();
  if (real != c.esperado) {
    Serial.printf("SD: %s mide %u bytes, se esperaban %u\n", c.ruta, (unsigned)real, (unsigned)c.esperado);
    return false;
  }
  return true;
}

// Guarda en la flash líneas ya firmadas, con el tipo de registro adelante ("D|" o "E|").
static void guardarPendientes(char tipo, const char *lineas, int n) {
  if (!flashOk || n == 0) {
    if (n) Serial.printf("Se perdieron %d filas: sin SD ni flash\n", n);
    return;
  }
  File f = LittleFS.open(RUTA_PENDIENTES, "a");
  if (!f || f.size() > PENDIENTES_MAX_BYTES) {
    if (f) f.close();
    Serial.printf("Se perdieron %d filas: respaldo en flash lleno\n", n);
    return;
  }
  for (int i = 0; i < n; i++) f.printf("%c|%s\n", tipo, lineas + i * LARGO_LINEA);
  f.close();
  filasPendientes += n;
  Serial.printf("Sin SD: %d filas guardadas en la flash (%lu pendientes)\n", n, (unsigned long)filasPendientes);
}

// Pasa a la SD las filas guardadas en la flash, un archivo a la vez, verificando
// cada uno. Si algo falla, conserva en la flash todo desde el archivo que falló.
static bool vaciarPendientes() {
  if (!flashOk || filasPendientes == 0) return true;
  File pend = LittleFS.open(RUTA_PENDIENTES, "r");
  if (!pend) {
    filasPendientes = 0;
    return true;
  }
  char linea[LARGO_LINEA];
  char abierto[13] = "";      // tipo + fecha del archivo abierto
  CsvAbierto dest;
  bool hayDest = false;
  size_t inicioArchivo = 0;   // posición en la flash donde empiezan las filas del archivo abierto
  uint32_t escritas = 0, enArchivo = 0;
  bool ok = true;
  while (pend.available()) {
    alimentarWDT();
    size_t pos = pend.position();
    if (leerLinea(pend, linea) < 12) continue;
    // Las filas de versiones anteriores no traen "D|" adelante.
    char tipo = linea[1] == '|' ? linea[0] : 'D';
    const char *fila = linea[1] == '|' ? linea + 2 : linea;
    char clave[13];
    snprintf(clave, sizeof(clave), "%c%.10s", tipo, fila);
    if (strcmp(clave, abierto) != 0) {
      if (hayDest) {
        hayDest = false;
        if (!cerrarVerificando(dest)) {
          ok = false;
          break;
        }
        escritas += enArchivo;
      }
      inicioArchivo = pos;
      enArchivo = 0;
      if (!abrirCsv(tipo, fila, dest)) {
        ok = false;
        break;
      }
      hayDest = true;
      snprintf(abierto, sizeof(abierto), "%s", clave);
    }
    if (!escribirCsv(dest, fila)) {
      ok = false;
      break;
    }
    enArchivo++;
  }
  if (hayDest) {
    if (cerrarVerificando(dest) && ok) escritas += enArchivo;
    else ok = false;
  }

  if (ok) {
    pend.close();
    LittleFS.remove(RUTA_PENDIENTES);
    filasPendientes = 0;
    Serial.printf("SD: %lu filas pendientes recuperadas desde la flash\n", (unsigned long)escritas);
    return true;
  }

  // Conservar desde el inicio del archivo que falló (puede quedar alguna fila
  // repetida en la SD al reintentar; la verificación de firmas la marcaría).
  pend.seek(inicioArchivo);
  File resto = LittleFS.open(RUTA_PENDIENTES_TMP, "w");
  uint32_t quedan = 0;
  if (resto) {
    while (pend.available()) {
      alimentarWDT();
      if (leerLinea(pend, linea) >= 12) {
        resto.printf("%s\n", linea);
        quedan++;
      }
    }
    resto.close();
  }
  pend.close();
  if (resto) {
    LittleFS.remove(RUTA_PENDIENTES);
    LittleFS.rename(RUTA_PENDIENTES_TMP, RUTA_PENDIENTES);
    filasPendientes = quedan;
  }
  Serial.printf("SD fallo al recuperar: %lu escritas, %lu siguen en la flash\n", (unsigned long)escritas, (unsigned long)quedan);
  return false;
}

// Firma n líneas (contiguas, de LARGO_LINEA bytes) y las escribe en la SD,
// o en la flash si la SD no está o la escritura no se pudo verificar.
// Todas deben ser del mismo día.
static void escribirRegistros(char tipo, char *lineas, int n) {
  if (n == 0) return;
  for (int i = 0; i < n; i++) firmarLinea(tipo, lineas + i * LARGO_LINEA);
  guardarCadena();

  bool escrito = false;
  if (sdOk && vaciarPendientes()) {
    CsvAbierto c;
    if (abrirCsv(tipo, lineas, c)) {
      escrito = true;
      for (int i = 0; i < n; i++) {
        if (!escribirCsv(c, lineas + i * LARGO_LINEA)) escrito = false;
      }
      if (!cerrarVerificando(c)) escrito = false;
    }
  }
  if (!escrito) {
    if (sdOk) {
      Serial.println("No se pudo escribir en la micro SD");
      sdOk = false;
      registrarEvento("SD_ERROR", "escritura no verificada; se guarda en la flash");
    }
    guardarPendientes(tipo, lineas, n);
  }
}

// Escribe los eventos en cola (se encolan desde cualquier tarea, se escriben aquí).
// Escribe un lote de eventos agrupado por día (escribirRegistros abre un solo
// archivo por llamada).
// (filas de LARGO_LINEA bytes seguidas en memoria; puntero simple por los
// prototipos que genera Arduino)
static void escribirEventosPorDia(char *lote, int n) {
  int desde = 0;
  for (int i = 1; i <= n; i++) {
    if (i == n || strncmp(lote + i * LARGO_LINEA, lote + desde * LARGO_LINEA, 10) != 0) {
      escribirRegistros('E', lote + desde * LARGO_LINEA, i - desde);
      desde = i;
    }
  }
}

// Pone la hora real a un evento creado sin hora: ahora - tiempo transcurrido.
static void fecharEvento(char *linea, uint32_t ms) {
  if (strncmp(linea, "0000-00-00 00:00:00", 19) != 0) return;
  time_t t = time(nullptr) - (time_t)((millis() - ms) / 1000);
  struct tm tm;
  localtime_r(&t, &tm);
  char fecha[20];
  strftime(fecha, sizeof(fecha), "%Y-%m-%d %H:%M:%S", &tm);
  memcpy(linea, fecha, 19);
  strncat(linea, " (hora estimada)", LARGO_LINEA - strlen(linea) - 1);
}

// Eventos ocurridos sin hora válida (arranque sin reloj): esperan aquí, con su
// millis(), y se fechan hacia atrás cuando aparece la hora, en vez de quedar en
// un archivo "0000-00-00".
static char sinFecha[COLA_EVENTOS][LARGO_LINEA];
static uint32_t sinFechaMs[COLA_EVENTOS];
static int nSinFecha = 0;

static void procesarEventos() {
  static char lote[COLA_EVENTOS][LARGO_LINEA];
  static uint32_t loteMs[COLA_EVENTOS];
  int n = 0;
  uint32_t perdidos;
  portENTER_CRITICAL(&mux);
  while (colaIni != colaFin && n < COLA_EVENTOS) {
    memcpy(lote[n], colaEventos[colaIni], LARGO_LINEA);
    loteMs[n++] = colaMs[colaIni];
    colaIni = (colaIni + 1) % COLA_EVENTOS;
  }
  perdidos = eventosPerdidos;
  eventosPerdidos = 0;
  portEXIT_CRITICAL(&mux);
  if (perdidos) registrarEvento("EVENTOS_PERDIDOS", "%lu eventos no cupieron en la cola", (unsigned long)perdidos);

  if (!horaValida()) {
    for (int i = 0; i < n; i++) {
      if (nSinFecha < COLA_EVENTOS) {
        memcpy(sinFecha[nSinFecha], lote[i], LARGO_LINEA);
        sinFechaMs[nSinFecha++] = loteMs[i];
      } else {
        eventosPerdidos++;
      }
    }
    return;
  }

  if (nSinFecha) {
    for (int i = 0; i < nSinFecha; i++) fecharEvento(sinFecha[i], sinFechaMs[i]);
    escribirEventosPorDia(&sinFecha[0][0], nSinFecha);
    nSinFecha = 0;
  }
  for (int i = 0; i < n; i++) fecharEvento(lote[i], loteMs[i]);  // creados justo antes de tener hora
  escribirEventosPorDia(&lote[0][0], n);
}

// Arma una fila por sensor con datos recientes y la registra.
static void registrarDatos() {
  if (!horaValida()) return;

  char fecha[20];
  fechaActual(fecha);

  static Sensor copia[MAX_SENSORES];
  static char lineas[MAX_SENSORES][LARGO_LINEA];
  portENTER_CRITICAL(&mux);
  memcpy(copia, sensores, sizeof(copia));
  portEXIT_CRITICAL(&mux);

  int n = 0;
  for (int i = 0; i < MAX_SENSORES; i++) {
    const Sensor &s = copia[i];
    if (!s.usado || !(s.tieneTemp || s.tieneHum)) continue;
    uint32_t edadS = (millis() - s.ultimoMs) / 1000;
    if (edadS > (uint32_t)SIN_DATOS_MIN * 60) continue;  // no repetir datos viejos

    char nombre[32], ieee[24], temp[8] = "", hum[8] = "", bat[5] = "", corrT[8], corrH[8];
    nombreSensor(i, s.ieee, nombre, sizeof(nombre));
    ieeeATexto(s.ieee, ieee);
    if (s.tieneTemp) {
      snprintf(temp, sizeof(temp), "%.1f", s.temp);
      char *punto = strchr(temp, '.');
      if (punto) *punto = ',';  // decimal con coma
    }
    if (s.tieneHum) snprintf(hum, sizeof(hum), "%.0f", s.hum);
    // Corrección de calibración ya incluida en Temperatura y Humedad (valor del
    // sensor = valor registrado - corrección).
    snprintf(corrT, sizeof(corrT), "%.1f", correccionSensor(s.ieee, true));
    char *coma = strchr(corrT, '.');
    if (coma) *coma = ',';
    snprintf(corrH, sizeof(corrH), "%.0f", correccionSensor(s.ieee, false));
    if (s.tieneBat) snprintf(bat, sizeof(bat), "%u", s.bat);
    // Hora en que el sensor envió el valor (puede ser de hace varios minutos:
    // los sensores solo reportan cuando cambia algo o cada 40-60 min).
    char horaLectura[20];
    time_t lectura = time(nullptr) - edadS;
    struct tm tl;
    localtime_r(&lectura, &tl);
    strftime(horaLectura, sizeof(horaLectura), "%Y-%m-%d %H:%M:%S", &tl);
    snprintf(lineas[n++], LARGO_LINEA, "%s;%s;%d;%s;%s;%s;%s;%s;%s;%s;%s;%s", fecha, cfg.codigo, i + 1, nombre,
             perfilSensor(s.ieee).almacenamiento, ieee, temp, hum, corrT, corrH, bat, horaLectura);
  }
  escribirRegistros('D', &lineas[0][0], n);
  if (n && sdOk) Serial.printf("SD: %d filas del %.10s\n", n, fecha);
}

// ---- Latido: detectar períodos sin registro (apagado, cuelgue) ----

static void guardarLatido() {
  if (!flashOk || !horaValida()) return;
  File f = LittleFS.open(RUTA_LATIDO, "w");
  if (!f) return;
  f.printf("%lld\n", (long long)time(nullptr));
  f.close();
}

// ---- Último valor de cada sensor: sin esto, tras un reinicio un sensor no se
// registra hasta su próximo reporte (hasta ~60 min) ----

static const char *RUTA_ULTIMOS = "/ultimos2.bin";  // ultimos.bin: formato anterior, sin hora de inicio de alarma

static void guardarUltimos() {
  if (!flashOk || !horaValida()) return;
  static UltimoValor v[MAX_SENSORES];
  int n = 0;
  time_t ahora = time(nullptr);
  portENTER_CRITICAL(&mux);
  for (int i = 0; i < MAX_SENSORES; i++) {
    const Sensor &s = sensores[i];
    if (!s.usado || !(s.tieneTemp || s.tieneHum)) continue;
    UltimoValor &u = v[n++];
    memcpy(u.ieee, s.ieee, 8);
    u.temp = s.temp;
    u.hum = s.hum;
    u.lectura = (uint32_t)(ahora - (millis() - s.ultimoMs) / 1000);
    u.marcas = s.tieneTemp | s.tieneHum << 1 | s.enAlarma << 2 | s.enAlarmaHum << 3;
    u.alarmaTempDesde = s.alarmaTempDesde;
    u.alarmaHumDesde = s.alarmaHumDesde;
  }
  portEXIT_CRITICAL(&mux);
  File f = LittleFS.open(RUTA_ULTIMOS, "w");
  if (!f) return;
  f.write((const uint8_t *)v, n * sizeof(UltimoValor));
  f.close();
}

// Al arrancar (con la hora ya fijada): recupera los valores que aún no son viejos.
// El estado de alarma también se recupera, para no repetir el evento ALARMA_*.
static void cargarUltimos() {
  if (!flashOk || !horaValida()) return;
  if (LittleFS.exists("/ultimos.bin")) LittleFS.remove("/ultimos.bin");
  File f = LittleFS.open(RUTA_ULTIMOS, "r");
  if (!f) return;
  time_t ahora = time(nullptr);
  UltimoValor u;
  int recuperados = 0;
  while (f.read((uint8_t *)&u, sizeof(u)) == sizeof(u)) {
    long edad = (long)(ahora - (time_t)u.lectura);
    bool estabaEnAlarma = u.marcas & 12;
    if (edad < 0 || (edad > SIN_DATOS_MIN * 60L && !estabaEnAlarma)) continue;
    for (int i = 0; i < MAX_SENSORES; i++) {
      Sensor &s = sensores[i];
      if (!s.usado || memcmp(s.ieee, u.ieee, 8) != 0) continue;
      s.temp = u.temp;
      s.hum = u.hum;
      s.tieneTemp = u.marcas & 1;
      s.tieneHum = u.marcas & 2;
      s.enAlarma = u.marcas & 4;
      s.enAlarmaHum = u.marcas & 8;
      s.alarmaTempDesde = u.alarmaTempDesde;
      s.alarmaHumDesde = u.alarmaHumDesde;
      s.ultimoMs = millis() - (uint32_t)edad * 1000;  // las cuentas con millis() son módulo 2^32
      if (s.tieneTemp) evaluarAlarma(i, true);
      if (s.tieneHum) evaluarAlarma(i, false);
      recuperados++;
      break;
    }
  }
  f.close();
  Serial.printf("%d sensores con su ultimo valor recuperado\n", recuperados);
}

static const char *motivoReinicio() {
  switch (esp_reset_reason()) {
    case ESP_RST_POWERON: return "encendido";
    case ESP_RST_EXT: return "reset externo";
    case ESP_RST_SW: return "reinicio por software";
    case ESP_RST_PANIC: return "falla del programa (panic)";
    case ESP_RST_INT_WDT:
    case ESP_RST_TASK_WDT:
    case ESP_RST_WDT: return "watchdog (programa colgado)";
    case ESP_RST_BROWNOUT: return "baja tension";
    case ESP_RST_USB: return "reset por USB";
    default: return "otro";
  }
}

// Número de serie del equipo: la dirección EUI-64 grabada de fábrica en el chip
// (única y no modificable; es también la dirección Zigbee del monitor). Los 6
// primeros bytes no bastan: en el C6 contienen "FFFE" y lo único va al final.
// El código (cfg.codigo) es la etiqueta que le ponemos; la serie identifica la placa física.
static void serieEquipo(char *out) {
  uint8_t mac[8];
  esp_read_mac(mac, ESP_MAC_IEEE802154);
  for (int i = 0; i < 8; i++) sprintf(out + 2 * i, "%02X", mac[i]);
}

// Al arrancar: registra equipo, versión, motivo del reinicio y las correcciones de
// calibración vigentes.
static void registrarArranque() {
  char serie[17];
  serieEquipo(serie);
  registrarEvento("ARRANQUE", "%s serie %s firmware %s, motivo: %s", cfg.codigo, serie, VERSION_FIRMWARE,
                  motivoReinicio());
  if (eventoConfigInicial[0]) registrarEvento("CONFIG_INICIAL", "%s", eventoConfigInicial);
  // La NVS es de esta placa: si antes tenía otro código, quedó registrado.
  String anterior = prefs.getString("codigo", "");
  if (anterior != cfg.codigo) {
    if (anterior.length())
      registrarEvento("CODIGO_CAMBIADO", "serie %s: antes %s, ahora %s", serie, anterior.c_str(), cfg.codigo);
    prefs.putString("codigo", cfg.codigo);
  }
  if (!horaValida()) registrarEvento("SIN_HORA", "el reloj no tiene hora valida: no se registran datos");
  registrarEvento("CONFIG", "pantalla %s, buzzer temperatura %s, buzzer humedad %s, %d sensores configurados",
                  cfg.pantalla == 2 ? "2,4\"" : "1,9\"", cfg.buzzerTemp ? "si" : "no", cfg.buzzerHum ? "si" : "no",
                  cfg.nSensores);
  for (int i = 0; i < cfg.nSensores; i++) {
    const SensorCfg *n = &cfg.sensores[i];
    if (n->oculto) {
      registrarEvento("SENSOR_OCULTO", "%s (%s): fuera de servicio, sus datos se ignoran", n->nombre, n->ieee4);
      continue;
    }
    if (n->calibrado[0])
      registrarEvento("CALIBRACION", "%s (%s): correccion T %+.1f C, HR %+.0f %%, calibrado %s", n->nombre, n->ieee4,
                      correccionCfg(n, true), correccionCfg(n, false), n->calibrado);
    else
      registrarEvento("CALIBRACION", "%s (%s): sin calibracion registrada (correccion T %+.1f C, HR %+.0f %%)", n->nombre,
                      n->ieee4, correccionCfg(n, true), correccionCfg(n, false));
  }
}

// En el primer tramo con hora válida: registra cada fila programada que no se
// grabó desde el último latido (apagado, reinicio, arranque lento o sin hora).
static void revisarHueco(long tramoActual) {
  if (!flashOk) return;
  File f = LittleFS.open(RUTA_LATIDO, "r");
  if (!f) return;
  char linea[LARGO_LINEA];
  leerLinea(f, linea);
  f.close();
  time_t ultimo = (time_t)atoll(linea);
  if (ultimo < 1735689600) return;
  const long periodo = REGISTRO_CADA_MIN * 60L;
  long perdidas = tramoActual - ultimo / periodo;  // tramos cuya fila no se grabó
  if (perdidas <= 0) return;
  char desde[20], hasta[20];
  struct tm t;
  time_t primera = (ultimo / periodo + 1) * periodo, ultima = tramoActual * periodo;
  localtime_r(&primera, &t);
  strftime(desde, sizeof(desde), "%Y-%m-%d %H:%M", &t);
  localtime_r(&ultima, &t);
  strftime(hasta, sizeof(hasta), "%Y-%m-%d %H:%M", &t);
  registrarEvento("SIN_REGISTRO", "%ld fila(s) no registrada(s): de %s a %s", perdidas, desde, hasta);
}

// ---- Retiro seguro y detección de la tarjeta ----

static bool sdRetirada = false;       // se pidió retirarla: no se usa aunque siga puesta
static bool sdSacadaTrasRetiro = false;
static uint32_t sdRetiradaMs = 0;     // cuándo se pidió el retiro
static char avisoTexto[24] = "";      // mensaje temporal en la cabecera
static uint32_t avisoHastaMs = 0;

static void mostrarAviso(const char *txt) {
  snprintf(avisoTexto, sizeof(avisoTexto), "%s", txt);
  avisoHastaMs = millis() + AVISO_MS;
}

// Mantener el pulsador: deja la SD lista para sacarla. Si ya estaba retirada
// y no se sacó, la vuelve a activar.
static void alternarRetiroSD() {
  if (sdRetirada) {
    sdRetirada = false;
    if (iniciarSD()) {
      registrarEvento("SD_INSERTADA", "reactivada con el pulsador");
      vaciarPendientes();
      mostrarAviso("SD activa de nuevo");
    } else {
      mostrarAviso("No hay SD");
    }
    return;
  }
  if (!sdOk) {
    mostrarAviso("No hay SD");
    return;
  }
  vaciarPendientes();
  SD.end();
  sdOk = false;
  sdRetirada = true;
  sdSacadaTrasRetiro = false;
  sdRetiradaMs = millis();
  Serial.println("SD desmontada: se puede retirar");
  registrarEvento("SD_DESMONTADA", "retiro seguro con el pulsador");
  mostrarAviso("Ya puedes sacar la SD");
}

// Revisa cada pocos segundos si la tarjeta sigue ahí o si volvió.
static void revisarSD() {
  static uint32_t ultimaMs = 0;
  uint32_t cada = sdOk ? SD_REVISAR_CADA_MS : SD_REINTENTAR_CADA_MS;
  if (millis() - ultimaMs < cada) return;
  ultimaMs = millis();

  if (sdOk) {
    // Una lectura real del sector 0: falla si la tarjeta ya no está.
    static uint8_t sector[512];
    if (!SD.readRAW(sector, 0)) {
      SD.end();
      sdOk = false;
      Serial.println("SD retirada sin aviso: las filas se guardan en la flash");
      registrarEvento("SD_RETIRADA", "sin aviso; las filas se guardan en la flash");
      mostrarAviso("SD retirada");
    }
    return;
  }

  bool hayTarjeta = montarSD();
  bool noSeRetiro = false;
  if (sdRetirada) {
    // Esperar a que la saquen; cuando vuelva a aparecer, reactivarla.
    if (!hayTarjeta) {
      sdSacadaTrasRetiro = true;
      return;
    }
    // Sigue puesta: no usarla hasta SD_REACTIVAR_MIN; después se asume que no
    // la van a sacar (para no dejar las filas en la flash por días).
    if (!sdSacadaTrasRetiro && millis() - sdRetiradaMs < SD_REACTIVAR_MIN * 60000UL) {
      SD.end();
      return;
    }
    noSeRetiro = !sdSacadaTrasRetiro;
    sdRetirada = false;
  } else if (!hayTarjeta) {
    return;
  }
  sdOk = true;
  Serial.println(noSeRetiro ? "Micro SD reactivada: no se retiro" : "Micro SD insertada");
  if (noSeRetiro)
    registrarEvento("SD_INSERTADA", "no se retiro en %d min: se vuelve a usar; %lu filas pendientes en la flash",
                    SD_REACTIVAR_MIN, (unsigned long)filasPendientes);
  else
    registrarEvento("SD_INSERTADA", "%lu filas pendientes en la flash", (unsigned long)filasPendientes);
  mostrarAviso(noSeRetiro ? "SD activa de nuevo" : "SD insertada");
  vaciarPendientes();
}

// La fuente por defecto (6x8 px por carácter a tamaño 1) es la CP437, que trae las letras con
// tilde y la ñ. Los textos del firmware están en UTF-8: se pasan a CP437 antes de dibujarlos, así
// la pantalla puede escribir "miércoles", "batería" o "Material estéril" (redacción de las
// directrices de Fricke Store). Lo que no tiene equivalente se cambia por "?".
static void aCP437(const char *s, char *out, size_t len) {
  static const struct { uint16_t utf8; uint8_t cp; } TABLA[] = {
    {0xC3A1, 0xA0}, {0xC3A9, 0x82}, {0xC3AD, 0xA1}, {0xC3B3, 0xA2}, {0xC3BA, 0xA3}, {0xC3B1, 0xA4},
    {0xC391, 0xA5}, {0xC389, 0x90}, {0xC3BC, 0x81}, {0xC39C, 0x9A}, {0xC2B0, 0xF8}, {0xC381, 'A'},
    {0xC38D, 'I'}, {0xC393, 'O'}, {0xC39A, 'U'}, {0xC2BF, 0xA8}, {0xC2A1, 0xAD}};
  size_t n = 0;
  for (const uint8_t *c = (const uint8_t *)s; *c && n + 1 < len; c++) {
    if (*c < 0x80) { out[n++] = *c; continue; }
    uint8_t cp = '?';
    if ((*c & 0xE0) == 0xC0 && c[1]) {
      uint16_t par = (c[0] << 8) | c[1];
      for (auto &t : TABLA) if (t.utf8 == par) cp = t.cp;
      c++;
    } else {
      while ((c[1] & 0xC0) == 0x80) c++;  // carácter de 3 o 4 bytes: se salta
    }
    out[n++] = cp;
  }
  out[n] = '\0';
}

static void texto(int x, int y, const char *s, uint8_t tam, uint16_t color) {
  char cp[64];
  aCP437(s, cp, sizeof(cp));
  gfx->setTextSize(tam);
  gfx->setTextColor(color);
  gfx->setCursor(x, y);
  gfx->print(cp);
}

static int anchoTexto(const char *s, uint8_t tam) {
  int n = 0;
  for (const uint8_t *c = (const uint8_t *)s; *c; c++)
    if ((*c & 0xC0) != 0x80) n++;  // cuenta caracteres, no bytes UTF-8
  return n * 6 * tam;
}

static void textoDerecha(int xDer, int y, const char *s, uint8_t tam, uint16_t color) {
  texto(xDer - anchoTexto(s, tam), y, s, tam, color);
}

// Corta el texto a maxCar caracteres (no bytes), para que no pase bajo el ícono de la cabecera.
static void recortar(char *s, int maxCar) {
  int n = 0;
  for (char *c = s; *c; c++) {
    if ((*c & 0xC0) == 0x80) continue;  // byte de continuación UTF-8: sigue al carácter anterior
    if (n++ == maxCar) { *c = '\0'; return; }
  }
}

// Ícono de F+data (herramientas/generar_marca.py). Va píxel a píxel por el lienzo indexado; las
// esquinas transparentes no se dibujan, así queda bien sobre cualquier color de cabecera.
static void dibujarMarca(int x, int y) {
  for (int j = 0; j < MARCA_LADO; j++)
    for (int i = 0; i < MARCA_LADO; i++) {
      uint8_t k = pgm_read_byte(&MARCA_PIXELES[j * MARCA_LADO + i]);
      if (k != MARCA_TRANSPARENTE) gfx->drawPixel(x + i, y + j, MARCA_PALETA[k]);
    }
}

static void textoCentro(int y, const char *s, uint8_t tam, uint16_t color) {
  texto((ANCHO - anchoTexto(s, tam)) / 2, y, s, tam, color);
}

// Color según el perfil: rojo fuera del rango de alarma, amarillo cerca del
// límite (o en la tolerancia, como 24-30 °C en farmacia), verde en rango.
static uint16_t colorSegunPerfil(float v, float min, float max, float avisoMin, float avisoMax) {
  if (v > max || (min > SIN_LIMITE && v < min)) return C_CALOR;
  if (v > avisoMax || (avisoMin > SIN_LIMITE && v < avisoMin)) return C_AVISO;
  return C_NORMAL;
}

static uint16_t colorTemp(float t, const Perfil &p) {
  return colorSegunPerfil(t, p.tempMin, p.tempMax, p.tempAvisoMin, p.tempAvisoMax);
}

static void antiguedad(uint32_t ms, char *out, size_t len) {
  uint32_t s = (millis() - ms) / 1000;
  if (s < 60) snprintf(out, len, "ahora");
  else if (s < 3600) snprintf(out, len, "hace %lum", (unsigned long)(s / 60));
  else snprintf(out, len, "hace %luh", (unsigned long)(s / 3600));
}

static bool sinDatos(const Sensor &s);

// Ícono de pila (18x9) alineado a la derecha en xDer, con el % a su izquierda.
// En gris si el % no está confirmado (viene de la memoria, antes del reinicio);
// vacía y sin % si el sensor no está reportando.
static void dibujarBateria(int xDer, int y, const Sensor &s) {
  const int ancho = 16, alto = 9;
  int x = xDer - ancho - 2;
  bool mostrar = s.tieneBat && !sinDatos(s);
  bool confirmada = mostrar && !s.batGuardada;
  uint16_t c = !confirmada               ? C_TENUE
               : s.bat < BATERIA_BAJA     ? C_CALOR
               : s.bat < BATERIA_ATENCION ? C_AVISO
                                          : C_NORMAL;
  gfx->drawRect(x, y, ancho, alto, c);
  gfx->fillRect(x + ancho, y + 2, 2, alto - 4, c);
  if (!mostrar) return;
  int relleno = (ancho - 4) * s.bat / 100;
  if (relleno < 1 && s.bat > 0) relleno = 1;
  gfx->fillRect(x + 2, y + 2, relleno, alto - 4, c);
  char buf[6];
  snprintf(buf, sizeof(buf), "%u%%", s.bat);
  // El % toma el color de la pila salvo en verde, donde queda en gris para no recargar la fila.
  textoDerecha(x - 3, y + 1, buf, 1, c == C_NORMAL ? C_TENUE : c);
}

// Una alarma sigue activa hasta que llegue una lectura dentro del rango. Si el sensor deja
// de reportar más de SIN_DATOS_MIN, revisarAvisosTecnicos() la cierra en silencio (firmware
// 2.3): el sensor queda marcado "sin datos" en pantalla, como cualquier sensor mudo.
static bool alarmaActiva(const Sensor &s) {
  return s.enAlarma || s.enAlarmaHum;
}

// Sin datos: no reporta hace más de SIN_DATOS_MIN (o nunca desde el arranque).
static bool sinDatos(const Sensor &s) {
  const uint32_t limite = (uint32_t)SIN_DATOS_MIN * 60000UL;
  if (s.tieneTemp || s.tieneHum) return millis() - s.ultimoMs > limite;
  return millis() > limite;
}

static bool bateriaBaja(const Sensor &s) {
  return s.tieneBat && s.bat < BATERIA_BAJA;
}

static uint16_t colorHum(float h, const Perfil &p) {
  return colorSegunPerfil(h, p.humMin, p.humMax, p.humAvisoMin, p.humAvisoMax);
}

static void dibujarFila(int y, int idx, const Sensor &s) {
  char nombre[32], edad[16], buf[12];
  nombreSensor(idx, s.ieee, nombre, sizeof(nombre));

  bool hayDatos = s.tieneTemp || s.tieneHum;
  bool viejo = hayDatos && (millis() - s.ultimoMs) > (uint32_t)SIN_DATOS_MIN * 60000UL;

  // Alarma: la fila parpadea en rojo (se redibuja una vez por segundo).
  bool alarma = alarmaActiva(s);
  bool fondoRojo = alarma && (millis() / 1000) % 2 == 0;
  if (fondoRojo) gfx->fillRect(0, y, ANCHO, ALTO_FILA - 1, C_ALARMA_FONDO);

  // Nombre y, a su lado, la etiqueta de color del tipo de almacenamiento. El
  // nombre se acorta si no deja espacio a la etiqueta antes del % de batería.
  const Perfil &perfil = perfilSensor(s.ieee);
  nombre[15 + (ANCHO - 170) / 6] = '\0';  // 15 caracteres en 1,9"; 26 en 2,4"
  texto(4, y + 4, nombre, 1, C_TEXTO);
  int xEtiqueta = 4 + anchoTexto(nombre, 1) + 5;
  gfx->fillRoundRect(xEtiqueta - 4, y + 3, anchoTexto(perfil.etiqueta, 1) + 7, 10, 5, perfil.colorEtiqueta);  // chip en píldora
  texto(xEtiqueta, y + 4, perfil.etiqueta, 1, C_TEXTO);
  dibujarBateria(ANCHO - 4, y + 3, s);

  if (hayDatos) antiguedad(s.ultimoMs, edad, sizeof(edad));
  else snprintf(edad, sizeof(edad), "esperando");
  textoDerecha(ANCHO - 4, y + ALTO_FILA - 10, edad, 1, viejo ? C_CALOR : C_TENUE);

  int yVal = y + 18;
  if (s.tieneTemp) {
    snprintf(buf, sizeof(buf), "%.1f", s.temp);
    bool fuera = alarma && s.enAlarma;  // el valor que activó la alarma: blanco sobre rojo intenso
    uint16_t c = fuera || fondoRojo ? C_TEXTO : viejo ? C_TENUE : colorTemp(s.temp, perfilSensor(s.ieee));
    if (fuera) gfx->fillRect(1, yVal - 3, anchoTexto(buf, 3) + 26, 27, C_ALARMA_VIVO);
    texto(4, yVal, buf, 3, c);
    int x = 4 + anchoTexto(buf, 3) + 4;
    gfx->drawCircle(x + 2, yVal + 2, 2, c);
    texto(x + 7, yVal, "C", 2, c);
  } else {
    texto(4, yVal, "--.-", 3, C_TENUE);
  }

  if (s.tieneHum) {
    snprintf(buf, sizeof(buf), "%.0f%%", s.hum);
    bool fuera = alarma && s.enAlarmaHum;
    uint16_t c = fuera || fondoRojo ? C_TEXTO : viejo ? C_TENUE : colorHum(s.hum, perfilSensor(s.ieee));
    if (fuera) gfx->fillRect(ANCHO - 7 - anchoTexto(buf, 2), yVal + 3, anchoTexto(buf, 2) + 6, 20, C_ALARMA_VIVO);
    textoDerecha(ANCHO - 4, yVal + 6, buf, 2, c);
  } else {
    textoDerecha(ANCHO - 4, yVal + 6, "--%", 2, C_TENUE);
  }

  gfx->drawFastHLine(0, y + ALTO_FILA - 1, ANCHO, C_LINEA);
}

// Alerta técnica de la SD a pantalla completa (amarilla, parpadea).
static void dibujarVistaSD() {
  char buf[32];
  bool vivo = (millis() / 1000) % 2 == 0;
  // Fondo naranja fijo (colores de la paleta) y franja superior que parpadea.
  gfx->fillScreen(C_AVISO);
  gfx->fillRect(0, 0, ANCHO, 40, C_FONDO);
  bool retirada = sdRetirada;
  uint16_t cTitulo = vivo ? C_AVISO : C_TEXTO;
  if (retirada) textoCentro(13, "SD RETIRADA", 2, cTitulo);
  else textoCentro(9, "FALLA SD", 3, cTitulo);
  if (retirada) {
    textoCentro(56, "Vuelve a poner", 2, C_FONDO);
    textoCentro(76, "la tarjeta SD", 2, C_FONDO);
  } else {
    textoCentro(56, "La tarjeta no", 2, C_FONDO);
    textoCentro(76, "responde", 2, C_FONDO);
    textoCentro(104, "Sácala y vuelve a", 1, C_FONDO);
    textoCentro(116, "ponerla en la ranura", 1, C_FONDO);
  }
  textoCentro(144, "Los datos se guardan", 1, C_FONDO);
  textoCentro(156, "en la memoria interna", 1, C_FONDO);
  snprintf(buf, sizeof(buf), "%lu filas pendientes", (unsigned long)filasPendientes);
  textoCentro(176, buf, 1, C_FONDO);
  gfx->drawFastHLine(10, 222, ANCHO - 20, C_FONDO);
  if (sdFueraDesde) {
    char hora[16];
    horaCorta(sdFueraDesde, hora, sizeof(hora));
    textoCentro(230, "sin SD desde", 1, C_FONDO);
    textoCentro(242, hora, 2, C_FONDO);
  }
  if (nivelBuzzer() == 1) textoCentro(ALTO - 20, "Pulsa para silenciar", 1, C_FONDO);
}

// Alerta de corte de luz a pantalla completa (firmware 2.4): el monitor quedó con la batería
// del módulo UPS. Mismo diseño que la alerta de la SD; suena como alarma hasta silenciarla.
static void dibujarVistaSinLuz() {
  char buf[32];
  bool vivo = (millis() / 1000) % 2 == 0;
  gfx->fillScreen(C_AVISO);
  gfx->fillRect(0, 0, ANCHO, 40, C_FONDO);
  textoCentro(9, "SIN LUZ", 3, vivo ? C_AVISO : C_TEXTO);
  textoCentro(56, "Funciona con", 2, C_FONDO);
  textoCentro(76, "la batería", 2, C_FONDO);
  textoCentro(104, "Revisa que el cargador", 1, C_FONDO);
  textoCentro(116, "esté enchufado", 1, C_FONDO);
  textoCentro(144, "Las mediciones y las", 1, C_FONDO);
  textoCentro(156, "alarmas siguen activas", 1, C_FONDO);
  gfx->drawFastHLine(10, 222, ANCHO - 20, C_FONDO);
  uint32_t min = (millis() - sinRedDesdeMs) / 60000;
  if (horaValida()) {
    char hora[16];
    horaCorta(time(nullptr) - (millis() - sinRedDesdeMs) / 1000, hora, sizeof(hora));
    textoCentro(230, "sin luz desde", 1, C_FONDO);
    textoCentro(242, hora, 2, C_FONDO);
  }
  snprintf(buf, sizeof(buf), "hace %lu min", (unsigned long)min);
  textoCentro(264, buf, 1, C_FONDO);
  if (nivelBuzzer() > 0) textoCentro(ALTO - 20, "Pulsa para silenciar", 1, C_FONDO);
}

// "14:50" si es de hoy, "28/09 14:50" si es de otro día.
static void horaCorta(time_t t, char *out, size_t len) {
  time_t ahora = time(nullptr);
  struct tm tt, th;
  localtime_r(&t, &tt);
  localtime_r(&ahora, &th);
  bool hoy = tt.tm_yday == th.tm_yday && tt.tm_year == th.tm_year;
  strftime(out, len, hoy ? "%H:%M" : "%d/%m %H:%M", &tt);
}

// Vista de alarma a pantalla completa: sensor, variable, valor en grande, límite
// y desde cuándo. Fondo parpadeante para que se note desde lejos.
static void dibujarVistaAlarma(int idx, const Sensor &s, bool esTemp, int num, int total) {
  char buf[32], nombre[32];
  bool vivo = (millis() / 1000) % 2 == 0;
  gfx->fillScreen(vivo ? C_ALARMA_VIVO : C_ALARMA_OSCURO);
  gfx->fillRect(0, 0, ANCHO, 40, C_TEXTO);
  textoCentro(9, "ALARMA", 3, C_ALARMA_VIVO);

  // A tamaño 2 caben 14 caracteres por línea: un nombre más largo se parte en
  // dos líneas en el último espacio ("Material" / "esteril").
  nombreSensor(idx, s.ieee, nombre, sizeof(nombre));
  const int porLinea = ANCHO / 12;
  char *corte = nullptr;
  if ((int)strlen(nombre) > porLinea) {
    for (char *c = nombre; *c && c - nombre <= porLinea; c++)
      if (*c == ' ') corte = c;
  }
  if (corte) {
    *corte = '\0';
    char *segunda = corte + 1;
    if ((int)strlen(segunda) > porLinea) segunda[porLinea] = '\0';
    textoCentro(50, nombre, 2, C_TEXTO);
    textoCentro(70, segunda, 2, C_TEXTO);
    textoCentro(94, perfilSensor(s.ieee).almacenamiento, 1, C_TEXTO);
  } else {
    nombre[porLinea] = '\0';
    textoCentro(58, nombre, 2, C_TEXTO);
    textoCentro(82, perfilSensor(s.ieee).almacenamiento, 1, C_TEXTO);
  }
  // Debajo del valor: qué variable es y el límite cruzado.
  textoCentro(170, esTemp ? "Temperatura" : "Humedad", 2, C_TEXTO);

  if (esTemp) {
    snprintf(buf, sizeof(buf), "%.1f", s.temp);
    int ancho = anchoTexto(buf, 5) + 6 + 18;  // número + símbolo de grado + "C"
    int x = (ANCHO - ancho) / 2;
    texto(x, 116, buf, 5, C_TEXTO);
    x += anchoTexto(buf, 5) + 5;
    gfx->drawCircle(x + 2, 118, 3, C_TEXTO);
    texto(x + 8, 116, "C", 3, C_TEXTO);
    const Perfil &p = perfilSensor(s.ieee);
    snprintf(buf, sizeof(buf), s.temp < p.tempMin ? "mínimo %.1f °C" : "máximo %.1f °C",
             s.temp < p.tempMin ? p.tempMin : p.tempMax);
  } else {
    snprintf(buf, sizeof(buf), "%.0f%%", s.hum);
    textoCentro(112, buf, 6, C_TEXTO);
    const Perfil &p = perfilSensor(s.ieee);
    bool baja = p.humMin > SIN_LIMITE && s.hum < p.humMin;
    snprintf(buf, sizeof(buf), baja ? "mínimo %.0f %%" : "máximo %.0f %%", baja ? p.humMin : p.humMax);
  }
  textoCentro(194, buf, 1, C_TEXTO);

  uint32_t desde = esTemp ? s.alarmaTempDesde : s.alarmaHumDesde;
  gfx->drawFastHLine(10, 222, ANCHO - 20, C_TEXTO);
  bool mudo = sinDatos(s);
  if (mudo && horaValida()) {
    // El valor de arriba es el último recibido: se aclara desde cuándo no hay datos.
    textoCentro(232, "SIN DATOS", 2, C_TEXTO);
    char hora[16];
    horaCorta(time(nullptr) - (millis() - s.ultimoMs) / 1000, hora, sizeof(hora));
    snprintf(buf, sizeof(buf), "último dato %s", hora);
    textoCentro(254, buf, 1, C_TEXTO);
    if (desde) {
      horaCorta(desde, hora, sizeof(hora));
      snprintf(buf, sizeof(buf), "alarma desde %s", hora);
      textoCentro(268, buf, 1, C_TEXTO);
    }
  } else if (desde && horaValida()) {
    // "desde" chico y la hora en grande: con la fecha ("28/09 14:50") no cabe
    // todo en una línea de tamaño 2.
    char hora[16];
    horaCorta(desde, hora, sizeof(hora));
    textoCentro(230, "desde", 1, C_TEXTO);
    textoCentro(242, hora, 2, C_TEXTO);
    long min = (long)(time(nullptr) - (time_t)desde) / 60;
    if (min < 0) min = 0;
    if (min < 60) snprintf(buf, sizeof(buf), "hace %ld min", min);
    else if (min < 1440) snprintf(buf, sizeof(buf), "hace %ld h %ld min", min / 60, min % 60);
    else snprintf(buf, sizeof(buf), "hace %ld d %ld h", min / 1440, (min % 1440) / 60);
    textoCentro(264, buf, 1, C_TEXTO);
  }
  if (total == 1) snprintf(buf, sizeof(buf), "1 alarma");
  else snprintf(buf, sizeof(buf), "%d de %d alarmas", num, total);
  textoCentro(ALTO - 20, buf, 1, C_TEXTO);
}

static void dibujar() {
  Sensor copia[MAX_SENSORES];
  int indices[MAX_SENSORES];
  int n = 0;
  portENTER_CRITICAL(&mux);
  // Los sensores en alarma van primero, para que ninguno quede en otra página.
  for (int pasada = 0; pasada < 2; pasada++) {
    for (int i = 0; i < MAX_SENSORES; i++) {
      if (!sensores[i].usado || alarmaActiva(sensores[i]) != (pasada == 0)) continue;
      copia[n] = sensores[i];
      indices[n++] = i;
    }
  }
  portEXIT_CRITICAL(&mux);

  int paginas = n == 0 ? 1 : (n + FILAS_POR_PAGINA - 1) / FILAS_POR_PAGINA;
  if (millis() - ultimoCambioPagina > CAMBIO_PAGINA_MS) {
    ultimoCambioPagina = millis();
    pagina = (pagina + 1) % paginas;
  }
  if (pagina >= paginas) pagina = 0;

  gfx->fillScreen(C_FONDO);

  // Cabecera: alarma (prioridad), aviso temporal (SD retirada, insertada...) u hora.
  int enAlarma = 0, primeraAlarma = -1;
  for (int i = 0; i < n; i++) {
    if (alarmaActiva(copia[i])) {
      if (primeraAlarma < 0) primeraAlarma = i;
      enAlarma++;
    }
  }
  bool aviso = (int32_t)(avisoHastaMs - millis()) > 0;

  // Pantalla de presentación (F+data, Fricke Store) cada LOGO_CADA_MIN, salvo con alarma, aviso, emparejamiento
  // o si alguien acaba de apretar un botón (quiere ver los sensores).
  bool emparejandoAhora = (int32_t)(emparejarHastaMs - millis()) > 0;
  bool usuarioMirando = (int32_t)(brilloAltoHastaMs - millis()) > 0;
  if (logoActivo(enAlarma || aviso || emparejandoAhora || usuarioMirando || alertaSDActiva() || sinRed)) {
    // El logo ocupa la pantalla completa: se copia directo al búfer del canvas.
    // El logo (16 bits, muchos colores) va directo al panel desde la flash, sin pasar por el canvas.
    panel->draw16bitRGBBitmap(0, 0, (uint16_t *)(ANCHO == 240 ? LOGO_PANTALLA_240 : LOGO_PANTALLA_170), ANCHO, ALTO);
    // Código del equipo y versión, en la franja libre bajo "Monitor de temperatura y humedad"
    // (herramientas/generar_logo.py deja libre esa franja).
    char txt[40];
    snprintf(txt, sizeof(txt), "Equipo %s  v%s", cfg.codigo, VERSION_FIRMWARE);
    panel->setTextSize(1);
    panel->setTextColor(C_TENUE);
    panel->setCursor((ANCHO - (int)strlen(txt) * 6) / 2, ANCHO == 240 ? 228 : 212);
    panel->print(txt);
    ultimoDesplazamiento = -1;  // al volver al canvas, limpiar el borde
    ajustarBrillo(false);
    return;
  }

  // Vista de alarma: alterna con la lista, rotando si hay varias (temperatura y
  // humedad de un mismo sensor cuentan por separado).
  if (enAlarma && !usuarioMirando && !emparejandoAhora) {
    const uint32_t ciclo = (ALARMA_PANTALLA_S + ALARMA_LISTA_S) * 1000UL;
    if (millis() % ciclo < ALARMA_PANTALLA_S * 1000UL) {
      int items[2 * MAX_SENSORES];  // i * 2 + (1 si es humedad)
      int total = 0;
      for (int i = 0; i < n; i++) {
        if (!alarmaActiva(copia[i])) continue;
        if (copia[i].enAlarma) items[total++] = i * 2;
        if (copia[i].enAlarmaHum) items[total++] = i * 2 + 1;
      }
      if (total > 0) {
        int k = (millis() / ciclo) % total;
        int i = items[k] / 2;
        dibujarVistaAlarma(indices[i], copia[i], items[k] % 2 == 0, k + 1, total);
        mostrarCanvas();
        ajustarBrillo(true);
        return;
      }
    }
  }

  // Corte de luz o alerta técnica de la SD (solo si no hay alarmas de sensores; la luz primero).
  // Con batería el brillo queda bajo (BRILLO_BATERIA) para que dure más.
  if (!enAlarma && (sinRed || alertaSDActiva()) && !usuarioMirando && !emparejandoAhora) {
    const uint32_t ciclo = (ALARMA_PANTALLA_S + ALARMA_LISTA_S) * 1000UL;
    if (millis() % ciclo < ALARMA_PANTALLA_S * 1000UL) {
      if (sinRed) dibujarVistaSinLuz();
      else dibujarVistaSD();
      mostrarCanvas();
      ajustarBrillo(!sinRed);
      return;
    }
  }

  gfx->fillRect(0, 0, ANCHO, ALTO_CABECERA, enAlarma ? C_ALARMA_FONDO : aviso ? C_AVISO_FONDO : C_CABECERA);
  // Ícono de F+data siempre visible a la derecha de la cabecera (firmware 2.3): 24 px, el mínimo
  // de las directrices, centrado en la altura y con su área de resguardo (6 px) libre alrededor.
  // Los textos de la cabecera se cortan antes de ese margen.
  const int xMarca = ANCHO - 6 - MARCA_LADO;
  const int libreDer = xMarca - 6;                // nada de la cabecera pasa de aquí
  const int maxCar = (libreDer - 4) / 6;          // caracteres de tamaño 1 que caben desde x = 4
  dibujarMarca(xMarca, (ALTO_CABECERA - MARCA_LADO) / 2);
  char buf[32];
  if (enAlarma) {
    char nombre[32];
    nombreSensor(indices[primeraAlarma], copia[primeraAlarma].ieee, nombre, sizeof(nombre));
    texto(4, 9, enAlarma > 1 ? "ALARMA (varios)" : "ALARMA", 1, C_TEXTO);
    const Sensor &a = copia[primeraAlarma];
    // Si no cabe, se acorta el nombre y nunca el valor.
    char valor[12];
    if (a.enAlarma) snprintf(valor, sizeof(valor), "%.1fC", a.temp);
    else snprintf(valor, sizeof(valor), "%.0f%% HR", a.hum);
    recortar(nombre, maxCar - (int)strlen(valor) - 1);
    snprintf(buf, sizeof(buf), "%s %s", nombre, valor);
    texto(4, 25, buf, 1, C_TEXTO);
  } else if (aviso) {
    snprintf(buf, sizeof(buf), "%s", avisoTexto);
    recortar(buf, maxCar);
    texto(4, 17, buf, 1, C_TEXTO);
  } else {
    // Fecha como pide la redacción de Fricke Store: "miércoles 18 nov 2026", hora en 24 h.
    static const char *DIAS[] = {"domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"};
    static const char *MESES[] = {"ene", "feb", "mar", "abr", "may", "jun", "jul",
                                  "ago", "sept", "oct", "nov", "dic"};
    char hora[6] = "--:--", fecha[32] = "sin fecha";
    if (horaValida()) {
      time_t ahora = time(nullptr);
      struct tm t;
      localtime_r(&ahora, &t);
      strftime(hora, sizeof(hora), "%H:%M", &t);
      snprintf(fecha, sizeof(fecha), "%s %d %s %d", DIAS[t.tm_wday], t.tm_mday, MESES[t.tm_mon], t.tm_year + 1900);
      // Con el ícono de F+data, "miércoles 30 sept 2026" no cabe en 1,9": el día va abreviado.
      static const char *DIAS_CORTOS[] = {"dom", "lun", "mar", "mié", "jue", "vie", "sáb"};
      if (4 + anchoTexto(fecha, 1) > libreDer)
        snprintf(fecha, sizeof(fecha), "%s %d %s %d", DIAS_CORTOS[t.tm_wday], t.tm_mday, MESES[t.tm_mon], t.tm_year + 1900);
    }
    texto(4, 5, hora, 2, C_TEXTO);
    texto(4, 27, fecha, 1, C_TEXTO);
  }
  // Indicador de la micro SD: verde si está grabando, amarillo si falta pero se
  // está guardando en la flash, rojo si no se puede guardar en ninguna parte.
  // Van a la izquierda del ícono de F+data.
  textoDerecha(libreDer, 9, "SD", 1, sdOk ? C_NORMAL : flashOk ? C_AVISO : C_CALOR);
  if (paginas > 1) {
    snprintf(buf, sizeof(buf), "%d/%d", pagina + 1, paginas);
    textoDerecha(libreDer - 12 - 8, 9, buf, 1, C_TEXTO);
  }

  if (n == 0) {
    texto(8, 70, "Sin sensores", 2, C_TEXTO);
    texto(8, 110, "1. Doble pulsación en el", 1, C_TENUE);
    texto(8, 122, "   pulsador para emparejar", 1, C_TENUE);
    texto(8, 142, "2. Mantén el botón del", 1, C_TENUE);
    texto(8, 154, "   sensor 5 s hasta", 1, C_TENUE);
    texto(8, 166, "   que parpadee", 1, C_TENUE);
  } else {
    int desde = pagina * FILAS_POR_PAGINA;
    for (int f = 0; f < FILAS_POR_PAGINA && desde + f < n; f++) {
      dibujarFila(ALTO_CABECERA + f * ALTO_FILA, indices[desde + f], copia[desde + f]);
    }
  }

  // Barra inferior: cuenta regresiva del emparejamiento, o estado general.
  int yBarra = ALTO - ALTO_BARRA;
  bool emparejando = (int32_t)(emparejarHastaMs - millis()) > 0;
  if (emparejando) {
    gfx->fillRect(0, yBarra, ANCHO, ALTO_BARRA, C_EMPAREJA);
    snprintf(buf, sizeof(buf), "Emparejando: %lu s", (unsigned long)((emparejarHastaMs - millis()) / 1000));
    texto(4, yBarra + 4, buf, 1, C_TEXTO);
  } else {
    gfx->fillRect(0, yBarra, ANCHO, ALTO_BARRA, C_CABECERA);
    // Avisos técnicos, del más grave al menos grave; si no hay, el estado general.
    char nombre[32];
    buf[0] = '\0';
    if (silencioVigente() && mascaraAlarmas())
      snprintf(buf, sizeof(buf), "Silenciado %lu min", (unsigned long)((silencioHastaMs - millis()) / 60000 + 1));
    else if (sinRed)
      snprintf(buf, sizeof(buf), "! Sin luz: batería %lu min", (unsigned long)((millis() - sinRedDesdeMs) / 60000));
    else if (!horaValida()) snprintf(buf, sizeof(buf), "! Reloj sin hora");
    else if (rtcFalla) snprintf(buf, sizeof(buf), "! Reloj no responde");
    else if (sdRetirada && !sdSacadaTrasRetiro) snprintf(buf, sizeof(buf), "! SD sin usar: pulsar 3 s");
    else if (!sdOk) snprintf(buf, sizeof(buf), "! Sin SD: datos en flash");
    for (int i = 0; i < n && !buf[0]; i++) {
      if (!sinDatos(copia[i])) continue;
      nombreSensor(indices[i], copia[i].ieee, nombre, sizeof(nombre));
      snprintf(buf, sizeof(buf), "! %.14s sin datos", nombre);
    }
    for (int i = 0; i < n && !buf[0]; i++) {
      if (!bateriaBaja(copia[i])) continue;
      nombreSensor(indices[i], copia[i].ieee, nombre, sizeof(nombre));
      snprintf(buf, sizeof(buf), "! %.13s batería baja", nombre);
    }
    if (buf[0]) {
      texto(4, yBarra + 4, buf, 1, C_AVISO);
    } else {
      snprintf(buf, sizeof(buf), "%d sensor%s", n, n == 1 ? "" : "es");
      texto(4, yBarra + 4, buf, 1, C_CLARO);  // gris claro: el gris tenue no se leía sobre el azul
      if (filasPendientes) {
        snprintf(buf, sizeof(buf), "%lu pend. SD", (unsigned long)filasPendientes);
        textoDerecha(ANCHO - 4, yBarra + 4, buf, 1, C_AVISO);
      }
    }
  }

  mostrarCanvas();
  ajustarBrillo(enAlarma > 0);
}

// Envía la imagen a la pantalla desplazada hasta 1 px, cambiando de posición cada
// DESPLAZAR_CADA_MIN, para que el contenido fijo no quede "marcado" en el panel.
static void mostrarCanvas() {
  static const int8_t desplazamientos[][2] = {{0, 0}, {1, 0}, {1, 1}, {0, 1}, {-1, 1}, {-1, 0}, {-1, -1}, {0, -1}, {1, -1}};
  int i = (millis() / (DESPLAZAR_CADA_MIN * 60000UL)) % 9;
  if (i != ultimoDesplazamiento) {
    panel->fillScreen(C_FONDO);  // limpia el borde que queda descubierto
    ultimoDesplazamiento = i;
  }
  // Recorte propio: si una parte queda fuera, la librería dibujaría píxel a píxel (muy lento).
  int16_t dx = desplazamientos[i][0], dy = desplazamientos[i][1];
  int16_t w = ANCHO - abs(dx), h = ALTO - abs(dy), salto = ANCHO - w;
  uint8_t *fb = gfx->getFramebuffer() + (dy < 0 ? -dy : 0) * ANCHO + (dx < 0 ? -dx : 0);
  int16_t x0 = dx > 0 ? dx : 0, y0 = dy > 0 ? dy : 0;
  panel->drawIndexedBitmap(x0, y0, fb, gfx->getColorIndex(), w, h, salto);
}

// Brillo de la luz de fondo: alto con alarma o tras apretar un botón, bajo de noche.
static void ajustarBrillo(bool hayAlarma) {
  static int actual = -1;
  int pct = BRILLO_NORMAL;
  if (hayAlarma || (int32_t)(brilloAltoHastaMs - millis()) > 0) {
    pct = BRILLO_ALTO;
  } else if (sinRed) {
    pct = BRILLO_BATERIA;  // con batería: bajo, para que dure más
  } else if (horaValida()) {
    time_t ahora = time(nullptr);
    struct tm t;
    localtime_r(&ahora, &t);
    bool noche = NOCHE_DESDE_H > NOCHE_HASTA_H ? (t.tm_hour >= NOCHE_DESDE_H || t.tm_hour < NOCHE_HASTA_H)
                                              : (t.tm_hour >= NOCHE_DESDE_H && t.tm_hour < NOCHE_HASTA_H);
    if (noche) pct = BRILLO_NOCHE;
  }
  if (pct != actual) {
    ledcWrite(TFT_BL, pct * 255 / 100);
    actual = pct;
  }
}

// ---- Buzzer y silencio ----
#define BIT_ALERTA_SD (1ULL << 63)   // alerta técnica de la SD (los sensores usan los bits bajos)
#define BIT_SIN_LUZ   (1ULL << 62)   // corte de luz: suena como alarma (firmware 2.4)
static_assert(2 * MAX_SENSORES <= 62, "los bits de los sensores chocan con el corte de luz y la SD");
// Alarmas que hacen sonar el buzzer, como bits: 2*i temperatura, 2*i+1 humedad
// del sensor i (según la configuración del equipo: buzzerTemp y buzzerHum).
static uint64_t mascaraAlarmas() {
  uint64_t m = 0;
  portENTER_CRITICAL(&mux);
  for (int i = 0; i < MAX_SENSORES; i++) {
    if (!sensores[i].usado) continue;
    if (cfg.buzzerTemp && sensores[i].enAlarma) m |= 1ULL << (2 * i);
    if (cfg.buzzerHum && sensores[i].enAlarmaHum) m |= 1ULL << (2 * i + 1);
  }
  portEXIT_CRITICAL(&mux);
  if (alertaSDActiva()) m |= BIT_ALERTA_SD;
  if (sinRed) m |= BIT_SIN_LUZ;
  return m;
}

static bool silencioVigente() {
  return mascaraSilenciada && (int32_t)(silencioHastaMs - millis()) > 0;
}

// Qué debe sonar: 0 nada, 1 alerta técnica (SD), 2 alarma de un sensor o corte de luz. Una
// alarma que aparece después de silenciar vuelve a sonar.
static int nivelBuzzer() {
#if BUZZER_PIN >= 0
  uint64_t m = mascaraAlarmas();
  mascaraSilenciada &= m;  // una alarma que terminó ya no cuenta como silenciada
  uint64_t sonando = silencioVigente() ? (m & ~mascaraSilenciada) : m;
  if (sonando & ~BIT_ALERTA_SD) return 2;
  if (sonando & BIT_ALERTA_SD) return 1;
#endif
  return 0;
}

static bool buzzerDebeSonar() {
  return nivelBuzzer() > 0;
}

static void silenciarAlarma() {
  uint64_t m = mascaraAlarmas();
  mascaraSilenciada = m;
  silencioHastaMs = millis() + SILENCIO_MIN * 60000UL;
  int n = 0;
  for (uint64_t b = m; b; b &= b - 1) n++;
  registrarEvento("ALARMA_SILENCIADA", "buzzer silenciado %d min con el pulsador (%d alarma(s) activas)", SILENCIO_MIN, n);
}

// Alarma de un sensor: 200 ms cada 2 s. Alerta técnica (SD): 100 ms cada 10 s.
static void sonarAlarma() {
#if BUZZER_PIN >= 0
  int nivel = nivelBuzzer();
  bool on = nivel == 2 ? millis() % 2000 < 200 : nivel == 1 ? millis() % 10000 < 100 : false;
  digitalWrite(BUZZER_PIN, on ? HIGH : LOW);
#endif
}

// Lleva la cuenta de cuánto tiempo la SD no graba y registra la alerta una vez.
static void revisarAlertaSD() {
  static bool registrada = false;
  envioPendientes = filasPendientes;
  if (sdOk) {
    sdFueraDesdeMs = 0;
    registrada = false;
    envioSdOk = 1;
    envioSdFueraS = 0;
    return;
  }
  if (!sdFueraDesdeMs) {
    sdFueraDesdeMs = millis() ? millis() : 1;
    sdFueraDesde = horaValida() ? time(nullptr) : 0;
  }
  envioSdOk = 0;
  envioSdFueraS = (millis() - sdFueraDesdeMs) / 1000;
  if (!registrada && alertaSDActiva()) {
    registrada = true;
    registrarEvento("SD_FALLA_PROLONGADA", "%s hace %d min, %lu filas esperando en la flash",
                    sdRetirada ? "SD retirada" : "la SD no responde", SD_ALERTA_MIN, (unsigned long)filasPendientes);
  }
}

// Registra un evento cuando un sensor deja de reportar o se le baja la batería,
// y otro cuando se recupera.
static void revisarAvisosTecnicos() {
  static uint32_t ultimaMs = 0;
  if (millis() - ultimaMs < 10000) return;
  ultimaMs = millis();
  for (int i = 0; i < MAX_SENSORES; i++) {
    portENTER_CRITICAL(&mux);
    Sensor s = sensores[i];
    portEXIT_CRITICAL(&mux);
    if (!s.usado) continue;

    char nombre[32];
    nombreSensor(i, s.ieee, nombre, sizeof(nombre));
    bool sd = sinDatos(s);
    if (sd != s.avisoSinDatos) {
      if (sd) registrarEvento("SENSOR_SIN_DATOS", "%s: sin reportar hace mas de %d min", nombre, SIN_DATOS_MIN);
      else registrarEvento("SENSOR_RECUPERADO", "%s: volvio a reportar", nombre);
    }
    // Sensor en alarma que se quedó mudo: la alarma se cierra en silencio, con su evento de fin.
    // Si vuelve a reportar fuera de rango, evaluarAlarma() la abre de nuevo.
    if (sd && (s.enAlarma || s.enAlarmaHum)) {
      portENTER_CRITICAL(&mux);
      sensores[i].enAlarma = false;
      sensores[i].enAlarmaHum = false;
      portEXIT_CRITICAL(&mux);
      alarmaCambio = true;
      if (s.enAlarma)
        registrarEvento("ALARMA_TEMP_FIN", "%s: sin datos hace mas de %d min, alarma cerrada", nombre, SIN_DATOS_MIN);
      if (s.enAlarmaHum)
        registrarEvento("ALARMA_HUM_FIN", "%s: sin datos hace mas de %d min, alarma cerrada", nombre, SIN_DATOS_MIN);
    }
    // Batería: se avisa bajo BATERIA_BAJA y se da por recuperada 5 puntos más arriba.
    bool bb = s.avisoBatBaja ? (s.tieneBat && s.bat < BATERIA_BAJA + 5) : bateriaBaja(s);
    if (bb != s.avisoBatBaja) {
      if (bb) registrarEvento("BATERIA_BAJA", "%s: %u %%", nombre, s.bat);
      else registrarEvento("BATERIA_OK", "%s: %u %%", nombre, s.bat);
    }
    portENTER_CRITICAL(&mux);
    sensores[i].avisoSinDatos = sd;
    sensores[i].avisoBatBaja = bb;
    portEXIT_CRITICAL(&mux);
  }
}

// ======================= Botón =======================

static void abrirEmparejamiento() {
  Zigbee.openNetwork(EMPAREJAR_SEGUNDOS);
  emparejarHastaMs = millis() + EMPAREJAR_SEGUNDOS * 1000UL;
  Serial.printf("Red abierta para emparejar durante %d s\n", EMPAREJAR_SEGUNDOS);
  registrarEvento("EMPAREJAMIENTO", "red abierta %d s", EMPAREJAR_SEGUNDOS);
}

// BOOT: solo sube el brillo. No empareja ni borra la red (eso se hace por USB con
// "BORRAR_RED SI", para que nadie pueda desconectar los sensores desde el panel).
static void revisarBoton() {
  if (digitalRead(BOTON_PIN) == LOW) pantallaActiva();
}

// Borra la red Zigbee y la lista de sensores (hay que volver a emparejarlos).
// Solo por el comando serie "BORRAR_RED SI".
static void borrarRed() {
  Serial.println("Borrando red Zigbee y sensores guardados...");
  registrarEvento("RED_BORRADA", "red Zigbee y lista de sensores borradas por USB");
  procesarEventos();
  gfx->fillScreen(C_FONDO);
  texto(8, 140, "Reiniciando red", 2, C_CALOR);
  gfx->flush();
  // Se borra la lista de sensores, pero no la clave de firma: la cadena sigue.
  prefs.remove("n");
  prefs.remove("ieee");
  prefs.remove("bat");
  Zigbee.factoryReset();  // reinicia la placa
}

// Pulsador externo (no borra la red, para que un toque accidental en el panel no
// pueda dejar a los sensores sin coordinador):
//   pulsación corta   -> brillo alto y siguiente página de sensores
//   doble pulsación   -> abre el emparejamiento
//   mantener RETIRAR_SD_MANTENER_MS -> retirar (o reactivar) la SD
static void revisarPulsadorEmparejar() {
  static bool anterior = HIGH;
  static uint32_t cambioMs = 0;
  static bool largaHecha = false;
  static bool visto_suelto = false;
  static bool clicPendiente = false;   // hubo un clic; se espera por si llega el segundo
  static uint32_t ultimoClicMs = 0;
  bool actual = digitalRead(PULSADOR_EMPAREJAR_PIN);
  static int8_t ultimoCrudo = -1;
  if (actual != ultimoCrudo) {
    ultimoCrudo = actual;
    Serial.printf("Pulsador (GPIO %d): %s\n", PULSADOR_EMPAREJAR_PIN, actual == LOW ? "presionado" : "suelto");
  }
  // Ignorarlo hasta verlo suelto una vez: si quedó conectado siempre cerrado,
  // no debe emparejar ni retirar la SD por su cuenta.
  if (!visto_suelto) {
    if (actual == HIGH) visto_suelto = true;
    anterior = actual;
    return;
  }
  if (actual != anterior && millis() - cambioMs > 50) {
    cambioMs = millis();
    anterior = actual;
    if (actual == LOW) {
      largaHecha = false;
      pantallaActiva();
    } else if (!largaHecha) {
      if (clicPendiente && millis() - ultimoClicMs < DOBLE_CLIC_MS) {
        clicPendiente = false;
        abrirEmparejamiento();
      } else {
        clicPendiente = true;
        ultimoClicMs = millis();
      }
    }
  }
  // Clic simple confirmado (no llegó un segundo): si el buzzer está sonando lo
  // silencia; si no, siguiente página.
  if (clicPendiente && actual == HIGH && millis() - ultimoClicMs >= DOBLE_CLIC_MS) {
    clicPendiente = false;
    if (buzzerDebeSonar()) {
      silenciarAlarma();
    } else {
      pagina++;
      ultimoCambioPagina = millis();
    }
  }
  if (actual == LOW && !largaHecha && millis() - cambioMs > RETIRAR_SD_MANTENER_MS) {
    largaHecha = true;
    clicPendiente = false;
    alternarRetiroSD();
  }
}

// ======================= Arduino =======================

// Comandos del Configurador (empiezan con @; respuestas con @ para distinguirlas
// del resto del monitor serie). Ver configurador/protocolo.md.
static void comandoConfigurador(const char *linea) {
  if (comandoWiFiConfigurador(linea)) return;
  char serie[17];
  serieEquipo(serie);
  if (strcmp(linea, "@INFO?") == 0) {
    char hora[20];
    fechaActual(hora);
    String s = "@INFO {\"codigo\":";
    jsonTexto(s, cfg.codigo);
    s += ",\"serie\":\"";
    s += serie;
    s += "\",\"firmware\":\"" VERSION_FIRMWARE "\",\"pantalla\":";
    s += cfg.pantalla;
    s += ",\"hora\":\"";
    s += hora;
    s += "\",\"hora_valida\":";
    s += horaValida() ? 1 : 0;
    s += ",\"unix\":";
    s += (long)(horaValida() ? time(nullptr) : 0);
    s += ",\"rtc\":";
    s += rtcOk ? 1 : 0;
    s += ",\"sd\":";
    s += sdOk ? 1 : 0;
    s += ",\"pendientes\":";
    s += (unsigned long)filasPendientes;
    s += ",\"energia_mv\":";
    s += (unsigned long)energiaMv;
    s += ",\"energia\":\"";
    s += !energiaArmada ? "sin_divisor" : sinRed ? "bateria" : "red";
    s += "\",\"sensores\":";
    s += contarSensores();
    s += ",\"wifi\":\"";
    s += !wifiRed[0] ? "no_configurado" : (wifiIniciado && WiFi.status() == WL_CONNECTED) ? "conectado" : wifiActivo ? "sin_conexion" : "apagado";
    s += "\"";
    s += ",\"emparejando\":";
    s += (int32_t)(emparejarHastaMs - millis()) > 0 ? (long)((emparejarHastaMs - millis()) / 1000) : 0;
    s += "}";
    Serial.println(s);
  } else if (strcmp(linea, "@CFG?") == 0) {
    String s = "@CFG_EQUIPO {\"codigo\":";
    jsonTexto(s, cfg.codigo);
    s += ",\"pantalla\":";
    s += cfg.pantalla;
    s += ",\"buzzer_temp\":";
    s += cfg.buzzerTemp;
    s += ",\"buzzer_hum\":";
    s += cfg.buzzerHum;
    s += "}";
    Serial.println(s);
    for (int i = 0; i < cfg.nSensores; i++) {
      const SensorCfg &c = cfg.sensores[i];
      String t = "@CFG_SENSOR {\"ieee4\":\"";
      t += c.ieee4;
      t += "\",\"nombre\":";
      jsonTexto(t, c.nombre);
      t += ",\"perfil\":\"";
      t += PERFIL_CODIGO[c.perfil ? 1 : 0];
      t += "\",\"corr_t\":";
      t += String(c.corrT10 / 10.0f, 1);
      t += ",\"corr_h\":";
      t += c.corrH;
      t += ",\"calibrado\":";
      jsonTexto(t, c.calibrado);
      t += ",\"oculto\":";
      t += c.oculto;
      t += "}";
      Serial.println(t);
    }
    Serial.println("@FIN");
  } else if (strcmp(linea, "@SENSORES?") == 0) {
    for (int i = 0; i < MAX_SENSORES; i++) {
      Sensor s;
      portENTER_CRITICAL(&mux);
      s = sensores[i];
      portEXIT_CRITICAL(&mux);
      if (!s.usado) continue;
      char ieee[24], ieee4[5], nombre[32];
      ieeeATexto(s.ieee, ieee);
      sprintf(ieee4, "%02X%02X", s.ieee[1], s.ieee[0]);
      nombreSensor(i, s.ieee, nombre, sizeof(nombre));
      String t = "@SENSOR {\"n\":";
      t += i + 1;
      t += ",\"ieee\":\"";
      t += ieee;
      t += "\",\"ieee4\":\"";
      t += ieee4;
      t += "\",\"nombre\":";
      jsonTexto(t, nombre);
      t += ",\"perfil\":\"";
      t += perfilSensor(s.ieee).etiqueta;
      t += "\",\"configurado\":";
      t += configSensor(s.ieee) ? 1 : 0;
      t += ",\"t\":";
      t += s.tieneTemp ? String(s.temp, 1) : String("null");
      t += ",\"h\":";
      t += s.tieneHum ? String(s.hum, 0) : String("null");
      t += ",\"bat\":";
      t += s.tieneBat ? String(s.bat) : String("null");
      t += ",\"edad\":";
      t += (s.tieneTemp || s.tieneHum) ? (long)((millis() - s.ultimoMs) / 1000) : -1;
      t += ",\"alarma\":";
      t += alarmaActiva(s) ? 1 : 0;
      t += "}";
      Serial.println(t);
    }
    Serial.println("@FIN");
  } else if (strncmp(linea, "@EQUIPO_SET ", 12) == 0) {
    // codigo|pantalla|buzzerTemp|buzzerHum
    char buf[64];
    snprintf(buf, sizeof(buf), "%s", linea + 12);
    char *codigo = strtok(buf, "|"), *pant = strtok(nullptr, "|"), *bt = strtok(nullptr, "|"), *bh = strtok(nullptr, "|");
    if (!codigo || !pant || !bt || !bh || !strlen(codigo) || strlen(codigo) > 15) {
      Serial.println("@ERROR formato: codigo|pantalla|buzzer_temp|buzzer_hum (codigo de 1 a 15 caracteres)");
      return;
    }
    char cod[16];
    snprintf(cod, sizeof(cod), "%s", codigo);
    limpiarTexto(cod);
    uint8_t pantalla = atoi(pant) == 2 ? 2 : 1;
    bool reiniciar = pantalla != cfg.pantalla;
    char antes[80];
    snprintf(antes, sizeof(antes), "%s/%d/%d/%d", cfg.codigo, cfg.pantalla, cfg.buzzerTemp, cfg.buzzerHum);
    bool cambioCodigo = strcmp(cod, cfg.codigo) != 0;
    portENTER_CRITICAL(&mux);
    snprintf(cfg.codigo, sizeof(cfg.codigo), "%s", cod);
    cfg.pantalla = pantalla;
    cfg.buzzerTemp = atoi(bt) ? 1 : 0;
    cfg.buzzerHum = atoi(bh) ? 1 : 0;
    portEXIT_CRITICAL(&mux);
    guardarConfig();
    registrarEvento("CONFIG_EQUIPO", "codigo/pantalla/buzzer T/buzzer H: %s -> %s/%d/%d/%d (Configurador)", antes,
                    cfg.codigo, cfg.pantalla, cfg.buzzerTemp, cfg.buzzerHum);
    if (cambioCodigo) prefs.putString("codigo", cfg.codigo);
    if (reiniciar) {
      Serial.println("@OK REINICIO");
      procesarEventos();
      Serial.flush();
      delay(500);
      ESP.restart();
    }
    Serial.println("@OK");
  } else if (strncmp(linea, "@SENSOR_SET ", 12) == 0) {
    SensorCfg s;
    const char *error = parsearSensor(linea + 12, s);
    if (error) {
      Serial.printf("@ERROR %s\n", error);
      return;
    }
    if (!ponerSensorCfg(s)) {
      Serial.println("@ERROR no caben mas sensores en la configuracion");
      return;
    }
    guardarConfig();
    registrarEvento("CONFIG_SENSOR", "%s: %s, %s, corr T %+.1f C, HR %+d %%, calibrado %s%s (Configurador)", s.ieee4,
                    s.nombre, PERFIL_CODIGO[s.perfil], s.corrT10 / 10.0f, s.corrH, s.calibrado[0] ? s.calibrado : "-",
                    s.oculto ? ", OCULTO" : "");
    listaCambio = true;
    Serial.println("@OK");
  } else if (strncmp(linea, "@SENSOR_DEL ", 12) == 0) {
    int i = buscarSensorCfg(linea + 12);
    if (i < 0) {
      Serial.println("@ERROR ese sensor no esta en la configuracion");
      return;
    }
    char ieee4[5], nombre[31];
    snprintf(ieee4, sizeof(ieee4), "%s", cfg.sensores[i].ieee4);
    snprintf(nombre, sizeof(nombre), "%s", cfg.sensores[i].nombre);
    portENTER_CRITICAL(&mux);
    for (int j = i; j < cfg.nSensores - 1; j++) cfg.sensores[j] = cfg.sensores[j + 1];
    cfg.nSensores--;
    portEXIT_CRITICAL(&mux);
    guardarConfig();
    registrarEvento("CONFIG_SENSOR_BORRADO", "%s (%s): vuelve a nombre y area por defecto, sin correccion (Configurador)",
                    ieee4, nombre);
    listaCambio = true;
    Serial.println("@OK");
  } else if (strncmp(linea, "@HORA ", 6) == 0) {
    Serial.println(fijarHoraUSB((time_t)atoll(linea + 6)) ? "@OK" : "@ERROR hora invalida");
  } else if (strcmp(linea, "@EMPAREJAR") == 0) {
    abrirEmparejamiento();
    Serial.println("@OK");
  } else if (strcmp(linea, "@EVENTOS?") == 0) {
    static char copia[EVENTOS_RECIENTES][LARGO_LINEA];
    int n, fin;
    portENTER_CRITICAL(&mux);
    memcpy(copia, eventosRecientes, sizeof(copia));
    n = eventosRecientesN;
    fin = eventosRecientesFin;
    portEXIT_CRITICAL(&mux);
    for (int k = 0; k < n; k++) Serial.printf("@EV %s\n", copia[(fin - n + k + EVENTOS_RECIENTES) % EVENTOS_RECIENTES]);
    Serial.println("@FIN");
  } else if (strcmp(linea, "@CLAVE?") == 0) {
    String s = "@CLAVE ";
    char hex[3];
    for (size_t i = 0; i < sizeof(claveFirma); i++) {
      sprintf(hex, "%02x", claveFirma[i]);
      s += hex;
    }
    Serial.println(s);
    registrarEvento("CLAVE_LEIDA", "se exporto la clave de firma por USB (Configurador)");
  } else if (strcmp(linea, "@REINICIAR") == 0) {
    Serial.println("@OK");
    registrarEvento("REINICIO_USB", "reinicio pedido desde el Configurador");
    procesarEventos();
    Serial.flush();
    delay(500);
    ESP.restart();
  } else {
    Serial.println("@ERROR comando desconocido");
  }
}

// ---- Respaldo de energía: ¿hay red eléctrica en la entrada del módulo UPS? ----
// La detección se activa sola (y queda guardada) cuando el pin muestra durante 10 s
// seguidos el voltaje del divisor: sin el divisor instalado, el pin al aire no debe
// generar avisos. Un cambio de estado se acepta tras 1,5 s estable.
static void revisarEnergia() {
#if ENERGIA_PIN >= 0
  static uint32_t ultimaMs = 0;
  static uint8_t estables = 0;
  if (millis() - ultimaMs < 500) return;
  ultimaMs = millis();
  energiaMv = analogReadMilliVolts(ENERGIA_PIN);
  bool hayRed = energiaMv > ENERGIA_UMBRAL_MV;
  if (!energiaArmada) {
    bool divisor = energiaMv > 1200 && energiaMv < 2200;  // ~1450 mV con 5 V en la entrada y el pull-down
    estables = divisor ? estables + 1 : 0;
    if (estables >= 20) {
      estables = 0;
      energiaArmada = true;
      prefs.putBool("energia", true);
      registrarEvento("RESPALDO_ENERGIA", "deteccion de corte de luz activada (%lu mV en la entrada)",
                      (unsigned long)energiaMv);
    }
    return;
  }
  if (hayRed != sinRed) {  // coincide con el estado actual
    estables = 0;
    return;
  }
  if (++estables < 3) return;
  estables = 0;
  sinRed = !hayRed;
  if (sinRed) {
    sinRedDesdeMs = millis();
    registrarEvento("CORTE_ENERGIA", "sin red electrica: el monitor funciona con la bateria del modulo UPS");
  } else {
    registrarEvento("ENERGIA_RESTABLECIDA", "volvio la red electrica tras %lu min con bateria",
                    (unsigned long)((millis() - sinRedDesdeMs) / 60000));
  }
#endif
}

void setup() {
  Serial.setTxBufferSize(2048);  // respuestas del Configurador de varias líneas
  Serial.begin(115200);
  // Por el USB nativo, si nadie lee el puerto el búfer se llena y cada print
  // esperaría: con 0 los mensajes se descartan en vez de bloquear el programa
  // (antes esto colgaba loop() y lo reiniciaba el watchdog).
  Serial.setTxTimeoutMs(0);
  pinMode(BOTON_PIN, INPUT_PULLUP);
  pinMode(PULSADOR_EMPAREJAR_PIN, INPUT_PULLUP);
#if BUZZER_PIN >= 0
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
#endif
  // Configuración del equipo (código, pantalla, buzzer, sensores): antes de crear la pantalla.
  {
    char serie[17];
    serieEquipo(serie);
    cargarConfig(serie);
  }
  crearPantalla();
  // Luz de fondo por PWM (brillo regulable); al arrancar, al máximo.
  ledcAttach(TFT_BL, 5000, 8);
  ledcWrite(TFT_BL, 255);
  pantallaActiva();

  if (!gfx->begin(TFT_SPI_HZ)) {
    Serial.println("No se pudo iniciar la pantalla (memoria para el canvas?)");
  }
  gfx->fillScreen(C_FONDO);
  texto(8, 140, "Iniciando...", 2, C_TEXTO);
  gfx->flush();

  prefs.begin("monitorth", false);
  energiaArmada = prefs.getBool("energia", false);
#if ENERGIA_PIN >= 0
  // Sin el divisor el pin queda al aire y el ADC lee cualquier cosa (se vio 1,3 V):
  // con el pull-down interno (~45 kΩ) lee 0 V. Con el divisor (20k/10k) baja apenas
  // de ~1,65 a ~1,45 V. Se activa después de la primera lectura, que configura el ADC.
  analogReadMilliVolts(ENERGIA_PIN);
  gpio_pulldown_en((gpio_num_t)ENERGIA_PIN);
#endif
  cargarClave();
  iniciarSD();  // después de la pantalla, que ya inició el bus SPI
  iniciarFlash();
  cargarCadena();
  setenv("TZ", ZONA_HORARIA, 1);
  tzset();
  // Hora: la del reloj RTC. Si no es válida, se fija desde el PC por el monitor serie.
  iniciarRTC();
  time_t desdeRTC = leerRTC();
  if (desdeRTC) {
    fijarHoraSistema(desdeRTC);
    Serial.println("Hora tomada del reloj RTC");
  } else {
    Serial.println("Sin hora. Envia por el monitor serie: HORA <segundos unix UTC>");
  }
  registrarArranque();
  if (!sdOk) registrarEvento("SD_AUSENTE", "al arrancar; las filas se guardan en la flash");

  cargarLista();
  cargarUltimos();

  zbCoordinador.allowMultipleBinding(true);
  zbCoordinador.setManufacturerAndModel("DIY", "MonitorTH");
  Zigbee.addEndpoint(&zbCoordinador);
  // La red NO se abre sola al arrancar: solo con BOOT o con el pulsador.

  if (!Zigbee.begin(ZIGBEE_COORDINATOR)) {
    Serial.println("Zigbee no arrancó, reiniciando...");
    delay(1000);
    ESP.restart();
  }
  {
    static esp_zb_nwk_neighbor_info_t v[MAX_SENSORES + 4];
    int n = leerVecinos(v, MAX_SENSORES + 4), hijos = 0;
    for (int i = 0; i < n; i++)
      if (v[i].relationship == ESP_ZB_NWK_RELATIONSHIP_CHILD) hijos++;
    registrarEvento("RED_AL_ARRANCAR", "%d de %d sensores siguen en la tabla de la red", hijos, contarSensores());
  }
  Serial.println("Coordinador Zigbee listo. Para emparejar: pulsador o BOOT, y mantener el botón del sensor ~5 s.");
  procesarEventos();
  // El latido se guarda en loop(), después de revisar si se perdieron filas.
  // Si loop() se cuelga más de WATCHDOG_S, la placa se reinicia (y queda registrado).
  esp_task_wdt_config_t wdt = {.timeout_ms = WATCHDOG_S * 1000, .idle_core_mask = 0, .trigger_panic = true};
  esp_task_wdt_reconfigure(&wdt);
  enableLoopWDT();
  wdtActivo = true;
  wifiAplicar(true);
  xTaskCreate(tareaWiFi, "wifi", 8192, nullptr, 1, nullptr);
}

void loop() {
  static uint32_t ultimaSync = 0, ultimoDibujo = 0;

  revisarBoton();
  revisarPulsadorEmparejar();
  revisarComandoSerie();
  revisarSD();

  if (millis() - ultimaSync > 2000) {
    ultimaSync = millis();
    sincronizarEnlazados();
  }
  atenderSensores();
  sonarAlarma();
  revisarAvisosTecnicos();
  procesarEventos();

  if (listaCambio || bateriaCambio) {
    listaCambio = false;
    bateriaCambio = false;
    guardarLista();
  }

  sincronizarConRTC();

  revisarAlertaSD();
  revisarEnergia();
  estadisticaZigbeeHora();

  if (alarmaCambio) {
    alarmaCambio = false;
    guardarUltimos();
  }

  // Registro en la SD alineado al reloj: 10:00, 10:05, 10:10...
  // Solo hacia adelante: si la corrección de hora retrocede el reloj, no se repite un tramo.
  static long ultimoTramo = -1;
  if (horaValida()) {
    long tramo = time(nullptr) / (REGISTRO_CADA_MIN * 60L);
    if (ultimoTramo != -1 && tramo < ultimoTramo - 2) ultimoTramo = tramo;  // la hora se ajustó muy atrás
    if (ultimoTramo == -1) revisarHueco(tramo);
    if (tramo > ultimoTramo) {
      if (ultimoTramo != -1) registrarDatos();
      ultimoTramo = tramo;
      guardarLatido();
      guardarUltimos();
    }
  }

  if (millis() - ultimoDibujo > 1000) {
    ultimoDibujo = millis();
    dibujar();
  }

  delay(10);
}

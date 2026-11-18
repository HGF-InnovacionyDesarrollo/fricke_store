#pragma once

// ======================= CONFIGURACIÓN DE CADA EQUIPO =======================
// Desde el firmware 2.0 el código del monitor (MTH-01, MTH-02...), el modelo de
// pantalla, qué alarmas suenan y la tabla de sensores (nombre, área, corrección,
// oculto) se guardan en la memoria de cada placa y se cambian con el Configurador
// (configurador/ConfiguradorMonitorTH.exe) por USB, sin compilar: un mismo
// firmware sirve para todos los monitores. config_inicial.h tiene los valores con
// que parten las placas que existían antes de la 2.0.
// Aquí quedan solo los ajustes comunes a todos los equipos.

// ---------- Pantalla ST7789 ----------
#define TFT_SCK   6
#define TFT_MOSI  7
#define TFT_CS    18
#define TFT_DC    19
#define TFT_RST   20
#define TFT_BL    21
#define TFT_SPI_HZ 40000000

// Brillo de la luz de fondo (%), para alargar su vida útil funcionando 24/7.
#define BRILLO_NORMAL    40
#define BRILLO_NOCHE     15    // entre NOCHE_DESDE_H y NOCHE_HASTA_H
#define BRILLO_ALTO      100   // con alguna alarma, o tras apretar un botón
#define BRILLO_ACTIVO_S  60    // segundos a brillo alto tras apretar un botón
#define NOCHE_DESDE_H    22
#define NOCHE_HASTA_H    7
// Cada cuánto se desplaza la imagen 1 px (evita retención de imagen en contenido fijo).
#define DESPLAZAR_CADA_MIN 60
// Pantalla de presentación con F+data y Fricke Store (logo_pantalla.h, generada con herramientas/generar_logo.py):
// se muestra LOGO_SEGUNDOS cada LOGO_CADA_MIN, salvo con alarmas o avisos.
#define LOGO_CADA_MIN      5
#define LOGO_SEGUNDOS      5
// Con alguna alarma, la pantalla alterna la vista de alarma (pantalla completa, en
// grande) con la lista de sensores. Tras apretar un botón se muestra solo la lista.
#define ALARMA_PANTALLA_S  5
#define ALARMA_LISTA_S     3

// ---------- Micro SD (comparte SCK y MOSI con la pantalla) ----------
#define SD_MISO   2
#define SD_CS     5
#define SD_SPI_HZ 20000000
#define REGISTRO_CADA_MIN 5   // una fila por sensor cada N minutos
// Si falta la SD, las filas se guardan en la flash interna hasta este tamaño
// (~10.000 filas: 3 sensores durante ~11 días) y se pasan a la SD cuando vuelve.
#define PENDIENTES_MAX_BYTES 1000000
#define SD_REVISAR_CADA_MS     5000   // con tarjeta: comprobar que sigue puesta
#define SD_REINTENTAR_CADA_MS  15000  // sin tarjeta: buscarla (cada intento bloquea ~1 s)
// Si tras pedir el retiro la tarjeta sigue puesta este tiempo, se vuelve a usar sola.
#define SD_REACTIVAR_MIN        5
#define RETIRAR_SD_MANTENER_MS 3000   // mantener el pulsador externo para retirar la SD
#define AVISO_MS               10000  // duración de los mensajes en la cabecera

// ---------- Reloj RTC DS3231 (I2C) ----------
// Guarda la hora con su pila. Se pone en hora desde el PC por USB enviando
// por el monitor serie:  HORA <segundos unix UTC>
#define RTC_SDA 10
#define RTC_SCL 11
#define ZONA_HORARIA "<-04>4<-03>,M9.1.6/24,M4.1.6/24"  // Chile continental

// ---------- Botones ----------
// BOOT de la placa: solo sube el brillo. Borrar la red se hace por USB con el
// comando "BORRAR_RED SI" (no hay forma de hacerlo desde los botones).
#define BOTON_PIN        BOOT_PIN

// Pulsador externo, entre este pin y GND (usa la pull-up interna):
//   corta: brillo alto y siguiente página | doble: emparejar | mantener: retirar la SD
#define PULSADOR_EMPAREJAR_PIN 23
#define DOBLE_CLIC_MS          700    // tiempo máximo entre las dos pulsaciones para emparejar

// ---------- Zigbee ----------
#define MAX_SENSORES          20
#define EMPAREJAR_SEGUNDOS    180   // tiempo que la red queda abierta al emparejar
#define CONFIGURAR_REPORTES   true  // pide a cada sensor nuevo que reporte más seguido
#define REPORTE_MIN_S         300   // cada reporte gasta pila: no más de uno cada 5 min
// Reporte aunque nada cambie. Con 600 s el Sensor 3 (que sí lo respeta) transmitía
// ~200 veces al día contra ~28 de los otros: gastaba pila de más. 30 min para
// farmacia y bodega estéril (salas con mucha inercia térmica). Los cambios de
// temperatura/humedad (REPORTE_DELTA_*) se siguen reportando apenas ocurren.
#define REPORTE_MAX_S         1800
#define REPORTE_DELTA_TEMP    0.2   // °C
#define REPORTE_DELTA_HUM     3.0   // %HR
#define REPORTE_BAT_MIN_S     3600
#define REPORTE_BAT_MAX_S     21600
#define LEER_BATERIA_CADA_H   6     // se vuelve a pedir tras una lectura si pasó este tiempo

// ---------- Presentación ----------
#define FILAS_POR_PAGINA      5
#define CAMBIO_PAGINA_MS      6000
// Sin lecturas en este tiempo -> "sin datos" (gris, aviso, evento, no se registra).
// Con la temperatura estable los UZ-5T reportan solo cada 40-60 min
// (REPORTE_MAX_S), así que el límite tiene que ser mayor que eso.
#define SIN_DATOS_MIN         75

// Cada cuánto se corrige la hora del C6 con la del DS3231 (el reloj interno del
// C6 se adelanta varios minutos por día). Sobre HORA_DERIVA_EVENTO_S se registra.
#define SINCRONIZAR_RTC_MIN   10
#define HORA_DERIVA_EVENTO_S  60

// Watchdog: si loop() no avanza en este tiempo, se reinicia la placa. Es holgado
// porque una SD con mal contacto puede demorar varios segundos en responder.
#define WATCHDOG_S            30

// ---------- Perfiles de umbrales (según protocolos del HGF) ----------
// Cada sensor usa un perfil (se elige en su configuración, con el Configurador). Colores:
//   verde entre avisoMin y avisoMax (inclusive) | amarillo fuera de eso |
//   rojo con alarma fuera de [min, max]. SIN_LIMITE desactiva ese lado.
// La alarma se apaga al volver dentro del rango con un margen de histéresis,
// para que no parpadee justo en el límite.
#define SIN_LIMITE             -1000.0
#define ALARMA_HISTERESIS      0.5   // °C
#define ALARMA_HUM_HISTERESIS  2.0   // %HR
struct Perfil {
  const char *nombre;                // en eventos
  const char *almacenamiento;        // columna "Almacenamiento" del CSV (admite tildes)
  float tempMin, tempMax;            // alarma bajo tempMin o sobre tempMax
  float tempAvisoMin, tempAvisoMax;  // verde entre estos valores
  float humMin, humMax;
  float humAvisoMin, humAvisoMax;
  const char *etiqueta;              // etiqueta junto al nombre en pantalla (3 letras)
  uint16_t colorEtiqueta;            // color RGB565 de su fondo
};
// APF 1.5 (medicamentos, §5.1.2): 15-25 °C, "hasta 30 °C por periodos breves";
// humedad no más de 60 %. Verde de 16 a 24 °C, amarillo sobre 24 °C, alarma sobre 30 °C.
static const Perfil PERFIL_MEDICAMENTOS = {
  "MEDICAMENTOS", "Medicamentos", 15.0, 30.0, 16.0, 24.0, SIN_LIMITE, 60.0, SIN_LIMITE, 55.0,
  "MED", 0x120D};  // --primario-suave #17406F (paleta de Fricke Store)
// APE 1.4 (material estéril, §5.1.1): 18-24 °C y humedad 30-50 %.
static const Perfil PERFIL_ESTERIL = {
  "MATERIAL ESTERIL", "Material estéril", 18.0, 24.0, 19.0, 23.0, 30.0, 50.0, 33.0, 47.0,
  "EST", 0x11E7};  // --acento-suave #123F39 (paleta de Fricke Store)
// Perfil de los sensores que no tienen configuración.
#define PERFIL_POR_DEFECTO PERFIL_MEDICAMENTOS
// Buzzer activo (TMB12A05) conectado directo: pata + a este pin, pata − a GND.
// -1 = sin buzzer.
#define BUZZER_PIN         22
// Una pulsación corta del pulsador mientras suena lo silencia este tiempo (la
// alarma sigue en pantalla). Una alarma nueva vuelve a sonar aunque esté silenciado.
#define SILENCIO_MIN       30
// Qué alarmas suenan (temperatura / humedad) se configura en cada equipo con el
// Configurador. La alerta técnica de la SD suena siempre.
// Alerta técnica si la SD lleva este tiempo sin funcionar (colgada o retirada):
// vista amarilla a pantalla completa y un pitido corto cada 10 s (silenciable).
#define SD_ALERTA_MIN      10

// ---------- Respaldo de energía (módulo UPS con celdas 18650) ----------
// Divisor 20 kΩ / 10 kΩ desde la ENTRADA de 5 V del módulo UPS (antes de la batería)
// a este pin con ADC: ~1,7 V con red eléctrica, 0 V con la luz cortada. -1 = sin
// detección. La detección se activa sola la primera vez que ve el voltaje del
// divisor (sin el divisor instalado el pin queda al aire y no debe dar avisos).
#define ENERGIA_PIN          3
#define ENERGIA_UMBRAL_MV    1000  // bajo este voltaje en el pin = sin red eléctrica
#define BRILLO_BATERIA       15    // % de brillo con batería (salvo alarma o botón), para que dure más

// Batería: verde desde BATERIA_ATENCION, amarillo bajo BATERIA_ATENCION,
// rojo (con aviso y evento) bajo BATERIA_BAJA.
#define BATERIA_ATENCION 40
#define BATERIA_BAJA     20
// La pila cae de voltaje justo después de transmitir. Se muestra el máximo
// de las últimas BATERIA_VENTANA_H a 2*BATERIA_VENTANA_H horas para no confundir
// esas caídas momentáneas con descarga real.
#define BATERIA_VENTANA_H 3

// ---------- Sensores ----------
// El nombre, el área (perfil MEDICAMENTOS o MATERIAL ESTERIL), la corrección de
// calibración y si está oculto se configuran en cada equipo con el Configurador.
// Calibración (docs/Instructivo_calibracion_sensores_Monitor_TH, procedimiento 7.4):
// la corrección se SUMA a lo que envía el sensor (promedio de referencia - sensor).
// Un sensor oculto se ignora (no se muestra, no se registra, no da alarmas ni
// avisos de "sin datos") sin borrarlo de la red Zigbee.
// Límite de seguridad: una corrección mayor se considera un error de tipeo y el
// Configurador no la acepta. Según el instructivo, una
// corrección mayor que la exactitud del sensor significa reemplazarlo.
#define CORRECCION_MAX_TEMP 3.0   // °C
#define CORRECCION_MAX_HUM  15.0  // %HR

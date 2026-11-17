# Operación de Fricke Store

## 0. Base de datos PostgreSQL

- **Producción:** un servidor PostgreSQL 16 o superior del hospital, en la red interna. Crear una base `fricke_store`
  y un usuario dueño con `CREATEROLE` (crea un rol por módulo) y `CREATEDB` (pruebas de restauración):

```sql
CREATE ROLE fricke LOGIN PASSWORD '…' CREATEROLE CREATEDB;
CREATE DATABASE fricke_store OWNER fricke;
```

- Configurar `ECO_DATABASE_URL=postgresql://fricke:…@servidor-bd:5432/fricke_store?sslmode=require` como variable
  de entorno del servicio (nunca en el repositorio). Al arrancar, el portal crea sus tablas (esquema `portal`) y las de cada módulo.
- **Traslado desde SQLite** (una sola vez): `python backend/gestionar.py importar-sqlite`. Copia usuarios, sesiones,
  solicitudes, módulos, incidentes y la bitácora con sus ids y hashes; al final verifica la cadena.
- **Desarrollo:** `docker compose up -d` levanta PostgreSQL en `localhost:5432` con la URL por defecto.

Cómo dejar el portal en condiciones de producción. Cubre las brechas técnicas del grupo A del informe normativo
(`reports/Requisitos normativos Fricke Store.md`): HTTPS (A4), respaldos (A7), monitoreo (A8), contención (A9) y bitácora en UTC con retención (A10).

## 1. HTTPS (A4)

1. Solicita a TI un certificado institucional para el nombre del servidor (por ejemplo `fricke-store.hospitalfricke.cl`).
2. Define las variables y arranca con el lanzador:

```bat
set ECO_TLS_CERT=C:\certs\fricke-store.pem
set ECO_TLS_KEY=C:\certs\fricke-store.key
python backend\servidor.py
```

- Sirve HTTPS en el puerto 8443 (configurable con `ECO_PUERTO_HTTPS`) con TLS 1.2 o superior y cifrados modernos.
- El puerto HTTP (8090, `ECO_PUERTO_HTTP`) solo redirige a HTTPS.
- Con HTTPS el portal envía `Strict-Transport-Security` y la cookie de sesión sale con `Secure`.
- Si se publica detrás de un proxy inverso (IIS, nginx), el proxy termina TLS y el lanzador acepta los encabezados `X-Forwarded-*`.

## 2. Respaldos cifrados (A7) — regla 3-2-1

```bash
python backend/respaldo.py crear     # pg_dump de toda la base, cifrado (Fernet/AES), con huella SHA-256 y rotación
python backend/respaldo.py probar    # lo restaura en una base temporal, verifica la bitácora y la borra
python backend/respaldo.py restaurar fricke-AAAAMMDDTHHMMSSZ.dump.gz.enc   # en una base nueva, nunca pisa la actual
```

- **Herramientas:** `pg_dump`/`pg_restore` de la misma versión mayor del servidor. Si PostgreSQL corre en Docker:
  `ECO_PG_DUMP="docker exec -i fricke-db pg_dump"` y `ECO_PG_RESTORE="docker exec -i fricke-db pg_restore"`.

- **Clave:** se genera en `data/respaldo.key` la primera vez. **Guarda una copia fuera del servidor** (bóveda de contraseñas o sobre sellado en Dirección). Sin ella, los respaldos no se pueden abrir.
- **Copia externa:** `ECO_RESPALDO_COPIA=\\servidor-respaldos\fricke-store` copia cada respaldo a otro equipo.
- **Tareas programadas (Windows):**

```bat
schtasks /Create /TN "FrickeStore Respaldo" /SC DAILY /ST 02:30 /TR "python C:\FrickeStore\backend\respaldo.py crear"
schtasks /Create /TN "FrickeStore Prueba restauracion" /SC MONTHLY /D 1 /ST 03:30 /TR "python C:\FrickeStore\backend\respaldo.py probar"
```

- El panel (**Administración › Seguridad y respaldos**) muestra el último respaldo y la última prueba. Genera una alerta si el respaldo tiene más de 26 horas o si no se ha probado una restauración en 3 meses.
- **Objetivos propuestos** (confirmar con un análisis de impacto): RPO de 24 horas (lo que se puede perder) y RTO de 4 horas (lo que puede tardar volver a operar). Si se necesita un RPO menor, programa respaldos cada 4 horas.

## 3. Monitoreo (A8)

- **Disponibilidad:** `GET /api/salud` responde `{"estado":"ok"}` (503 si la base falla). Úsalo en Uptime Kuma o Zabbix con una alerta por correo o Telegram.
- **Alertas dentro del portal:** el resumen de administración muestra:
  - ráfagas de intentos fallidos;
  - cuentas bloqueadas;
  - intentos desde muchas IP;
  - ingresos de cuentas privilegiadas de madrugada;
  - solicitudes de derechos por vencer;
  - plazos de incidentes vencidos;
  - respaldos atrasados.
- **SIEM:** cada evento de la bitácora se copia como JSON en `data/logs/auditoria.jsonl` (`ECO_LOG_SIEM`). Configura el agente de Wazuh o Graylog para leer ese archivo.

## 4. Contención (A9)

En **Administración › Seguridad y respaldos**, el administrador y el delegado de ciberseguridad pueden:

- cerrar todas las sesiones;
- forzar el cambio de contraseña a las cuentas privilegiadas;
- suspender o reanudar todos los módulos;
- pausar o reanudar los formularios públicos.

Cada acción pide la contraseña y un motivo, y queda en la bitácora. Estas acciones corresponden a la Instrucción General N° 4 de ANCI.

## 5. Bitácora: hora y retención (A10)

- Todos los registros se guardan en **UTC** (ISO 8601 con `+00:00`).
- **Sincronizar la hora** del servidor con el SHOA (DS 9/2023, art. 13):

```bat
w32tm /config /manualpeerlist:"ntp.shoa.cl" /syncfromflags:manual /reliable:YES /update
w32tm /resync
```

- **Retención:** 5 años (`ECO_RETENCION_BITACORA_DIAS=1825`), declarada en la política pública. Para archivar lo más antiguo sin romper la cadena:

```bash
python backend/gestionar.py archivar-bitacora
```

- El comando escribe un archivo JSONL sellado con SHA-256 en `data/archivo_bitacora/` y guarda un "ancla" para seguir verificando la integridad.
- **Guarda el sello fuera del servidor.**

## 6. Contraseñas

- **Política:** mínimo 15 caracteres y lista de contraseñas prohibidas (`backend/claves_bloqueadas.txt`), sin reglas de composición ni cambios periódicos forzados (NIST SP 800-63B rev. 4). Se exige cambiarla ante sospecha de compromiso.
- **Ampliar la lista:** agrega contraseñas comunes o filtradas, una por línea.
- **Algoritmo:** *scrypt* (N=2^14, r=8, p=1) es una función de derivación resistente a ataques por memoria, de la misma familia y nivel que Argon2. El DS 9/2023 (art. 6) admite Bcrypt, PBKDF2, SHA-3 y Argon2 "o superiores". La equivalencia queda justificada en este documento; migrar a Argon2id queda como mejora futura.

## 7. Perfiles

| Perfil | Puede |
|---|---|
| Funcionario | Usar los módulos asignados y *Mi cuenta* |
| Administrador | Todo, incluida la gestión de cuentas |
| Delegado de Protección de Datos | Derechos Ley 21.719, módulos (evaluación de impacto), incidentes y bitácora (lectura) |
| Delegado de Ciberseguridad | Incidentes, contención, respaldos, alertas y bitácora; **no gestiona cuentas** (independencia de TI, IG N° 3 de ANCI) |

Crear un delegado por consola:

```bash
python backend/gestionar.py crear --rut ... --nombre "..." --dpd
```

Para el delegado de ciberseguridad, créalo como funcionario y asígnale el perfil desde el panel.

## Segundo factor de autenticación (Microsoft Authenticator)

- **Obligatorio** para Administrador, Delegado de Protección de Datos y Delegado de Ciberseguridad (`ECO_MFA_PERFILES`).
  Un administrador puede **exigirlo** a cualquier otra persona en *Administración › Usuarios › Gestionar*.
- La primera vez, la persona escanea un QR con Microsoft Authenticator (o cualquier app TOTP) y recibe **8 códigos de respaldo** de un solo uso.
- Desde entonces, al ingresar se pide la contraseña y luego el código de 6 dígitos. Cinco códigos erróneos cierran el intento.
- **Si alguien pierde el celular:** verificar su identidad y usar *Restablecer (perdió el celular)* en el panel, o por consola
  `python backend/gestionar.py restablecer-mfa --rut …`. Volverá a escanear el QR al ingresar.
- Los secretos se guardan cifrados con `data/<establecimiento>/mfa.key`: **respaldar esa clave fuera del servidor**, igual que la de respaldos.
  Sin ella, todas las personas deberán volver a configurar su app.

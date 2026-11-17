# Fricke Store — ecosistema digital del Hospital Dr. Gustavo Fricke

> Este repositorio es la **plataforma común de la red**: el mismo código sirve a cada establecimiento con su propia
> instalación, marca, usuarios y base de datos (Fricke Store, Marga-Marga Store, …). Ver [docs/RED.md](docs/RED.md).

Portal de acceso único a las soluciones digitales del hospital, con el modelo visual de Google:
portada con un buscador (que será el **asistente de IA**, hoy maqueteado), **menú de puntos** con los módulos
del ecosistema y **tarjeta de cuenta** con avatar. Ingreso con **RUT y contraseña**.

Por ahora no tiene módulos: se irán agregando de a poco (ver *Agregar un módulo*).

## Qué incluye

- **Ingreso con RUT** validado (módulo 11) y formateado al escribir; mensajes de error que no revelan si el RUT existe.
- **Primer ingreso guiado**: cambio obligatorio de la contraseña temporal y lectura del aviso de privacidad.
- **Portada** estilo Google: logotipo, barra del asistente, sugerencias y una nota que recuerda no escribir datos de pacientes.
- **Menú de módulos** (los nueve puntos): solo muestra lo que tu perfil puede usar; hoy aparece vacío.
- **Bloqueo de pantalla** (`Ctrl+Alt+L` o desde la tarjeta de cuenta), pensado para equipos compartidos en las unidades clínicas.
- **Cierre por inactividad** con aviso un minuto antes.
- **Mi cuenta**, al estilo de la cuenta de Google: datos personales, sesiones abiertas con cierre remoto,
  actividad reciente, descarga de mis datos y solicitudes de derechos (Ley 21.719).
- **Bitácora inalterable**: cada registro está encadenado con SHA-256 al anterior.
- **Solicitar una cuenta** desde el login: la persona deja sus datos y un administrador la aprueba.
- **Recuperar contraseña**: el pedido llega al panel; la Mesa de ayuda verifica identidad y entrega una clave temporal.
- **Panel de administración** (`/admin`, desde la tarjeta de cuenta): resumen, usuarios (crear, editar, perfil,
  restablecer, desbloquear, desactivar, cerrar sesiones), solicitudes de cuenta, pedidos de contraseña,
  derechos Ley 21.719 con plazos, módulos con su ficha de tratamiento y bitácora con verificación de integridad.
- **Perfiles**: funcionario, administrador, Delegado de Protección de Datos y Delegado de Ciberseguridad.
- **Incidentes** con plazos de ANCI (3 h, 24/72 h, 7 y 15 días) y de la Agencia de Protección de Datos, con cuenta regresiva y alertas.
- **Contención** (IG N° 4 de ANCI): cerrar todas las sesiones, forzar cambio de claves privilegiadas, suspender módulos, pausar formularios.
- **Alertas de seguridad** en el resumen, endpoint `/api/salud` para monitores y copia JSON de la bitácora para un SIEM.
- **Respaldos cifrados** con prueba de restauración (`backend/respaldo.py`) y archivo sellado de la bitácora antigua.
- **HTTPS** con HSTS y redirección (`backend/servidor.py`).
- **Derechos Ley 21.719 con plazos legales**: acuse de recibo, 30 días corridos con una prórroga, bloqueo en 2 días hábiles, denegación con leyenda de reclamo y respuesta sellada.
- **Contraseñas según NIST SP 800-63B rev. 4**: 15 caracteres mínimo y lista de bloqueo, sin reglas de composición.

El detalle normativo está en [docs/CUMPLIMIENTO.md](docs/CUMPLIMIENTO.md); la puesta en producción, en [docs/OPERACION.md](docs/OPERACION.md);
las plantillas para firma del Director, en [docs/plantillas/](docs/plantillas/); y el informe completo, en [reports/](reports/).

## Ejecutar

Fricke Store usa **PostgreSQL** (esquema `portal` para el núcleo y uno por módulo). Para desarrollo hay un
`docker-compose.yml`; en producción se apunta `ECO_DATABASE_URL` al servidor del hospital.

```bash
docker compose up -d                # PostgreSQL de desarrollo en localhost:5432
pip install -r requirements.txt
python backend/gestionar.py importar-sqlite   # solo una vez, si vienes de la versión con SQLite
python backend/gestionar.py crear --rut 12.345.678-5 --nombre "Ana Pérez" --cargo "Enfermera" --unidad "UPC" --admin
python backend/servidor.py          # HTTP 8090; con ECO_TLS_CERT/ECO_TLS_KEY sirve HTTPS
```

Abrir http://localhost:8090 e ingresar con el RUT y la clave temporal que imprime el comando `crear`.
En Windows también sirve `iniciar.bat`.

## Cómo se crean las cuentas

1. La persona pulsa **Solicitar una cuenta** en el login, o un administrador la crea en **Administración › Usuarios**.
2. El administrador aprueba y el sistema muestra una **contraseña temporal una sola vez**.
3. Se entrega en persona; al primer ingreso se exige crear una contraseña propia y leer el aviso de privacidad.

No hay registro abierto ni envío de claves por correo: en un hospital la identidad se verifica antes de dar acceso.

## Administración (consola)

```bash
python backend/gestionar.py listar
python backend/gestionar.py restablecer --rut 12.345.678-5
python backend/gestionar.py desbloquear --rut 12.345.678-5
python backend/gestionar.py desactivar --rut 12.345.678-5
python backend/gestionar.py solicitudes
python backend/gestionar.py verificar-auditoria
```

## Configuración

Variables de entorno (ver `backend/config.py`): `ECO_DATABASE_URL` (PostgreSQL), `ECO_INSTITUCION`, `ECO_PRODUCTO` (palabra del logotipo),
`ECO_CORREO_DPD`, `ECO_MESA_AYUDA`, `ECO_INACTIVIDAD_MIN`, `ECO_SESION_MAX_H`, `ECO_COOKIE_SEGURA=1` (con HTTPS), `ECO_VERSION_AVISO`,
`ECO_DOMINIO_CORREO` (exige correo institucional en las solicitudes), `ECO_LIMITE_PUBLICO` y `ECO_VENTANA_PUBLICO_MIN` (límite de solicitudes por IP).

## Agregar un módulo

¿Vas a desarrollar un módulo desde tu PC? Parte por **[docs/COLABORAR.md](docs/COLABORAR.md)**.

Los módulos viven en `modulos/<clave>/` y siguen las **[directrices para módulos](docs/MODULOS.md)**: comparten el ingreso
con RUT, la cabecera con el logo, la bitácora encadenada y los respaldos, y declaran su ficha de tratamiento (Ley 21.719).

```bash
python backend/gestionar.py nuevo-modulo --clave farmacia --nombre "Farmacia" --familia 2   # parte desde el módulo de ejemplo
python backend/gestionar.py modulos                                             # valida, migra y lista
```

Al reiniciar el portal el módulo se registra solo, **inactivo**. Se publica en **Administración › Módulos** eligiendo quién lo ve.
Si trata datos de salud, no aparecerá hasta que el DPD apruebe la evaluación de impacto.
El ejemplo de referencia es `modulos/ejemplo/` (Tablón de avisos).

También se pueden registrar enlaces a sistemas externos desde **Administración › Módulos › Agregar módulo**, con su ficha de tratamiento.

## Estructura

```
backend/   app.py (API y páginas) · gestion.py (solicitudes y administración) · plataforma.py (módulos) · db.py (esquema y bitácora) · seguridad.py (RUT, scrypt, tokens) · gestionar.py · config.py
frontend/  index.html (portada) · login.html · cuenta.html · admin.html · privacidad.html · css/ · js/ (comun.js, cabecera.js) · img/
modulos/   un módulo por carpeta (ejemplo/ es la plantilla)
docs/      MODULOS.md (directrices) · CUMPLIMIENTO.md · OPERACION.md · HOJA_DE_RUTA.md
data/      respaldos, logs y claves locales (no se versiona). Los datos viven en PostgreSQL.
```

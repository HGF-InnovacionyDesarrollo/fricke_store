# Ecosistema hospitalario

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

El detalle normativo está en [docs/CUMPLIMIENTO.md](docs/CUMPLIMIENTO.md).

## Ejecutar

```bash
pip install -r requirements.txt
python backend/gestionar.py crear --rut 12.345.678-5 --nombre "Ana Pérez" --cargo "Enfermera" --unidad "UPC" --admin
python -m uvicorn app:app --app-dir backend --port 8090
```

Abrir http://localhost:8090 e ingresar con el RUT y la clave temporal que imprime el comando `crear`.
En Windows también sirve `iniciar.bat`.

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

Variables de entorno (ver `backend/config.py`): `ECO_INSTITUCION`, `ECO_PRODUCTO` (palabra del logotipo),
`ECO_CORREO_DPD`, `ECO_MESA_AYUDA`, `ECO_INACTIVIDAD_MIN`, `ECO_SESION_MAX_H`, `ECO_COOKIE_SEGURA=1` (con HTTPS), `ECO_VERSION_AVISO`.

## Agregar un módulo

Insertar una fila en `modulos` con su **finalidad** y **categorías de datos** (obligatorias) y habilitarlo por rol
(`modulos_rol`) o por persona (`modulos_usuario`). Si trata datos de salud, marcar `datos_sensibles=1`: no aparecerá en
el menú hasta que el DPD apruebe su evaluación de impacto (`eipd_aprobada=1`).

## Estructura

```
backend/   app.py (API y páginas) · db.py (esquema y bitácora) · seguridad.py (RUT, scrypt, tokens) · gestionar.py · config.py
frontend/  index.html (portada) · login.html · cuenta.html · privacidad.html · css/ · js/ · img/
docs/      CUMPLIMIENTO.md · HOJA_DE_RUTA.md
data/      ecosistema.db (no se versiona)
```

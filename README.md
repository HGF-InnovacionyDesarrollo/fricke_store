# Fricke Store — ecosistema digital del Hospital Dr. Gustavo Fricke

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
- **Perfiles**: funcionario, administrador y Delegado de Protección de Datos (DPD: derechos, módulos y bitácora).

El detalle normativo está en [docs/CUMPLIMIENTO.md](docs/CUMPLIMIENTO.md).

## Ejecutar

```bash
pip install -r requirements.txt
python backend/gestionar.py crear --rut 12.345.678-5 --nombre "Ana Pérez" --cargo "Enfermera" --unidad "UPC" --admin
python -m uvicorn app:app --app-dir backend --port 8090
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

Variables de entorno (ver `backend/config.py`): `ECO_INSTITUCION`, `ECO_PRODUCTO` (palabra del logotipo),
`ECO_CORREO_DPD`, `ECO_MESA_AYUDA`, `ECO_INACTIVIDAD_MIN`, `ECO_SESION_MAX_H`, `ECO_COOKIE_SEGURA=1` (con HTTPS), `ECO_VERSION_AVISO`,
`ECO_DOMINIO_CORREO` (exige correo institucional en las solicitudes), `ECO_LIMITE_PUBLICO` y `ECO_VENTANA_PUBLICO_MIN` (límite de solicitudes por IP).

## Agregar un módulo

En **Administración › Módulos › Agregar módulo**: nombre, dirección, ícono, color, perfiles que lo ven y su
**ficha de tratamiento** (finalidad y categorías de datos, obligatorias). Si trata datos de salud, marcar
*datos sensibles*: no aparecerá en el menú hasta que se marque la evaluación de impacto como aprobada.

## Estructura

```
backend/   app.py (API y páginas) · gestion.py (solicitudes y administración) · db.py (esquema y bitácora) · seguridad.py (RUT, scrypt, tokens) · gestionar.py · config.py
frontend/  index.html (portada) · login.html · cuenta.html · admin.html · privacidad.html · css/ · js/ · img/
docs/      CUMPLIMIENTO.md · HOJA_DE_RUTA.md
data/      ecosistema.db (no se versiona)
```

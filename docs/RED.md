# Plataforma de la red: un código, una instalación por establecimiento

El ecosistema es **una sola plataforma** para toda la red asistencial. Cada hospital corre **su propia instalación**
del mismo código, con su nombre, logo, colores, usuarios y base de datos:

| Establecimiento | Clave | Producto | Base de datos |
|---|---|---|---|
| Hospital Dr. Gustavo Fricke | `fricke` | Fricke Store | `fricke_store` |
| Hospital Marga-Marga | `marga_marga` | Marga-Marga Store | `marga_marga_store` |

## Qué es común y qué es de cada establecimiento

| Común a la red (el repositorio) | Propio de cada establecimiento |
|---|---|
| Código del portal (`backend/`, `frontend/`) | `establecimientos/<clave>/establecimiento.json`: nombre, producto, unidad desarrolladora, Director(a), DPD, mesa de ayuda, dominio de correo, colores |
| Módulos (`modulos/`) y sus directrices (`docs/MODULOS.md`) | `establecimientos/<clave>/marca/`: logo e íconos |
| Cumplimiento y operación (`docs/`) | Su base PostgreSQL, sus usuarios, sus datos y su bitácora |
| `establecimientos/red.json`: datos de la red | Qué módulos activa y quién los ve (panel de administración) |

Por qué así (Ley 21.719 y continuidad): cada hospital administra sus cuentas, su DPD ve solo lo suyo, los datos no se
mezclan y un incidente o una caída en una instalación no afecta a las demás. Un módulo se programa una sola vez y
cada hospital decide si lo publica.

Una persona que trabaja en dos hospitales tiene una cuenta en cada uno (mismo RUT, contraseñas independientes).
Un ingreso único para toda la red, conectado al directorio del Servicio de Salud, queda como mejora futura.

## Elegir el establecimiento

La variable `ECO_ESTABLECIMIENTO` indica qué establecimiento atiende la instalación (por defecto `fricke`).
De ella salen, salvo que se sobrescriban con su propia variable `ECO_*`:

- la base de datos `postgresql://…/<clave>_store`,
- la carpeta local `data/<clave>/` (logs, respaldos y clave de cifrado),
- la cookie de sesión `eco_sesion_<clave>`, los roles de módulo `<clave>_m_<módulo>` y el prefijo de los respaldos.

```bat
iniciar.bat                 :: Fricke Store en el puerto 8090
iniciar.bat marga_marga 8091 :: Marga-Marga Store en el puerto 8091
```

## Agregar un establecimiento

```bash
python backend/gestionar.py nuevo-establecimiento --clave quillota --producto "Quillota Store" --institucion "Hospital San Martín de Quillota"
docker exec fricke-db createdb -U fricke quillota_store      # en desarrollo; en producción lo crea TI
ECO_ESTABLECIMIENTO=quillota python backend/gestionar.py crear --rut … --nombre … --admin
```

Luego completar su `establecimiento.json` (DPD, Director(a), mesa de ayuda, colores con contraste AA) y poner su logo
en `marca/` (`icono.svg`, `logo-icono.svg`, `favicon-32.png`, `apple-touch-icon.png`, `favicon.ico`).

## Pendientes por establecimiento

- **Marga-Marga:** logo oficial (hoy hay uno provisional sin símbolo), unidad desarrolladora, correo del DPD y mesa de ayuda.
- **Red:** nombre oficial del Servicio de Salud en `establecimientos/red.json`, y confirmar con jurídica quién es el responsable
  de los datos (probablemente el Servicio de Salud) para ajustar el aviso de privacidad.

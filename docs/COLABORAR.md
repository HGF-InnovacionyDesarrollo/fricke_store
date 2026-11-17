# Cómo sumar un módulo desde tu PC

Guía para quien desarrolla un módulo de Fricke Store en su propio computador. Trabajas en tu copia del proyecto,
con tu propia base de datos vacía, y entregas el módulo con un *pull request* que revisa la Unidad de Innovación y
Desarrollo. Nunca necesitas los datos reales del hospital ni acceso al PC de otra persona.

## 1. Pide acceso

Pide a la Unidad que te agregue al repositorio
[HGF-InnovacionyDesarrollo/fricke_store](https://github.com/HGF-InnovacionyDesarrollo/fricke_store)
con tu cuenta de GitHub. Te llegará una invitación por correo.

## 2. Prepara tu PC (una sola vez)

Instala:

- [Git](https://git-scm.com/downloads)
- [Python 3.12 o superior](https://www.python.org/downloads/) (marca "Add Python to PATH" al instalar)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (para la base de datos de desarrollo)
- Opcional: [Claude Code](https://claude.com/claude-code). El archivo `CLAUDE.md` del proyecto ya le indica las reglas.

Luego, en una terminal:

```bash
git clone https://github.com/HGF-InnovacionyDesarrollo/fricke_store.git
cd fricke_store
pip install -r requirements.txt
docker compose up -d
```

`docker compose up -d` crea **tu propia** base PostgreSQL vacía en tu PC. Los datos reales nunca están en el
repositorio: la carpeta `data/` y las bases no se suben.

## 3. Crea tu cuenta de prueba y abre el portal

```bash
python backend/gestionar.py crear --rut 11.111.111-1 --nombre "Tu Nombre" --admin
iniciar.bat
```

Abre http://localhost:8090 e ingresa con el RUT y la clave temporal que imprimió `crear`. Como administrador, el
portal te pedirá configurar Microsoft Authenticator la primera vez. Usa un RUT de prueba, no el tuyo real.

## 4. Crea tu módulo en una rama propia

```bash
git checkout main
git pull
git checkout -b modulo/farmacia
python backend/gestionar.py nuevo-modulo --clave farmacia --nombre "Farmacia" --familia 2
```

- La **familia** (1 a 5) y el **pictograma** del ícono se eligen según las
  [directrices de diseño](diseno/README.md). Con `--pictograma archivo.svg` usas un ícono de
  [Lucide](https://lucide.dev); si no, queda uno provisional que debes cambiar antes de entregar.
- El comando copia el módulo de ejemplo a `modulos/farmacia/`. Desde ahí sigue
  [docs/MODULOS.md](MODULOS.md): ficha de tratamiento, migraciones, API y pantallas.
- **En esta etapa ningún módulo maneja datos de pacientes**: el portal no carga un módulo cuya ficha los mencione.
- Para verlo en el portal: reinicia `iniciar.bat`, entra a **Administración › Módulos**, marca tu módulo como
  activo y elige quién lo ve.
- `python backend/gestionar.py modulos` revisa que tu módulo cargue sin errores.

Toca solo tu carpeta `modulos/<clave>/` y el ícono generado. Si necesitas cambiar algo común (`backend/`,
`frontend/`, `docs/`), conversa antes con la Unidad.

## 5. Corre las pruebas

```bash
pip install -r requirements-dev.txt   # una sola vez
pytest
```

Revisan solas que tu módulo cumpla las reglas comunes (sesión, perfiles, ícono, diseño, datos personales) y corren
las pruebas propias de tu módulo en `modulos/<clave>/tests/`. Si algo falla, el mensaje dice qué regla y en qué
archivo. GitHub corre lo mismo en cada *pull request*: si falla, no se puede integrar.

## 6. Entrega con un pull request

```bash
git add modulos/farmacia docs/logo/modulos/farmacia frontend/img/modulos/farmacia.svg
git commit -m "feat(farmacia): primera versión del módulo"
git push -u origin modulo/farmacia
```

GitHub te mostrará un enlace para abrir el *pull request* hacia `main`. La descripción trae la checklist de las
directrices: márcala con honestidad, adjunta capturas en modo claro y oscuro, a 360 y 1440 px. La Unidad lo revisa,
te deja comentarios y, cuando esté aprobado, lo integra. Mientras tanto puedes seguir subiendo cambios a la misma rama.

## Reglas que no se negocian

- Nunca subas `data/`, contraseñas, claves ni datos reales de personas.
- Todo endpoint usa `acceso(...)` y toda acción relevante queda en la bitácora sin RUT en el detalle.
- Colores solo desde `base.css`; el logo de Fricke Store no se modifica.
- Mantén tu rama al día: `git pull origin main` antes de pedir revisión.

## Si algo falla

| Problema | Qué hacer |
|---|---|
| El portal no arranca: no conecta a la base | Abre Docker Desktop y ejecuta `docker compose up -d` |
| `nuevo-modulo` no genera los PNG del ícono | Necesita Google Chrome o Microsoft Edge instalado |
| Tu módulo no aparece en el menú | Revisa `gestionar.py modulos` y actívalo en Administración › Módulos |
| `pytest` falla al conectar a la base | Abre Docker Desktop: las pruebas crean su propia base desechable |
| Quedaste fuera por el segundo factor | `python backend/gestionar.py restablecer-mfa --rut 11.111.111-1` |

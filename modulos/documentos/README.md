# F+docs (documentos)

Biblioteca de documentos institucionales del hospital en PDF (protocolos, normas, guías, instructivos, circulares),
ordenados en carpetas y con buscador.

Pedido por: Unidad de Innovación y Desarrollo (nov 2026). Familia 5, Personas y gestión. Pictograma `folder-open`
de Lucide.

## Qué hace

| Pantalla | Para qué |
|---|---|
| Documentos | Carpetas y subcarpetas con migas de pan. Cada PDF se abre en una pestaña nueva o se descarga. |
| Buscar | Busca en título, descripción, nombre del archivo y carpetas, sin importar tildes ni mayúsculas. Dirección `/m/documentos/buscar?q=…`. A esta pantalla lleva el botón **Buscar un documento** de la pantalla de inicio del portal. |
| Papelera | Documentos eliminados de los últimos 30 días y el historial de versiones reemplazadas (5 años): abrir, restaurar o eliminar para siempre. |
| Acerca del módulo | Qué hace, quién lo administra y la ficha de tratamiento. |

- **Solo PDF**, hasta 25 MB cada uno. Se guardan en la base del módulo (`m_documentos.versiones`), así que entran en
  los respaldos del portal sin hacer nada extra.
- **Reemplazar** un PDF deja la versión anterior 5 años en el historial (para saber qué versión estaba vigente en cada fecha, como pide la acreditación); se puede restaurar.
- **Eliminar** un documento lo manda a la papelera 30 días. `depurar()` (que corre con `gestionar.py depurar`) la vacía.
- **Carpetas**: solo se eliminan vacías (no pasan por la papelera). Si un documento de la papelera estaba en una carpeta
  que ya no existe, al restaurarlo vuelve al inicio.

## Permisos

| Permiso | Quién | Qué permite |
|---|---|---|
| `documentos.ver` | perfiles `funcionario` y `admin` | Ver, buscar, abrir y descargar. |
| `documentos.administrar` | nadie por defecto: **persona a persona** | Crear, renombrar, mover y eliminar carpetas; subir, editar, reemplazar y eliminar documentos; papelera. |

Para dar el permiso de administrar a alguien:

```bash
python backend/gestionar.py permiso --rut 12.345.678-5 --permiso documentos.administrar
python backend/gestionar.py permiso --rut 12.345.678-5 --permiso documentos.administrar --revocar
```

## Datos personales (Ley 21.719)

Solo guarda el id interno de quien crea carpetas y sube, cambia o elimina documentos, con la fecha. Los documentos son
institucionales: al subir se muestra el aviso de no subir documentos con datos de pacientes ni de otras personas.
`exportar_titular` entrega lo que la persona hizo (sin los PDF) y `depurar` vacía la papelera a los 30 días y el historial de versiones a los 5 años.
En la bitácora queda la acción con el número de documento o carpeta, nunca el título ni el contenido.

## Cómo probarlo

1. **Administración › Módulos › F+docs**: marcar *Activo* (viene habilitado para `funcionario` y `admin`).
2. Dar `documentos.administrar` a una persona de prueba con el comando de arriba.
3. Con esa persona: crear carpetas y subir PDF. Con otra: ver, buscar y descargar.
4. `pytest modulos/documentos`.

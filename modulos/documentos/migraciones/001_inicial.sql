-- Esquema inicial de F+docs (dentro de m_documentos, con el rol del módulo).
-- Una migración aplicada NO se edita: los cambios van en 002_*.sql. Sin BEGIN/COMMIT: el portal ya usa una transacción.
-- Las personas se referencian por usuarios.id del portal (nunca el RUT). Fechas en TIMESTAMPTZ.
-- Papelera: un documento eliminado guarda eliminado_en; una versión reemplazada guarda reemplazada_en.
-- depurar() borra ambos a los 30 días.

CREATE TABLE carpetas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    padre_id BIGINT REFERENCES carpetas (id) ON DELETE RESTRICT,     -- NULL: carpeta en el inicio
    nombre TEXT NOT NULL CHECK (length(btrim(nombre)) BETWEEN 1 AND 80),
    creada_por BIGINT NOT NULL,                                       -- usuarios.id del portal (otro esquema: sin FK)
    creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (padre_id IS NULL OR padre_id <> id)
);
-- Dos carpetas hermanas no pueden llamarse igual (sin distinguir mayúsculas).
CREATE UNIQUE INDEX ux_carpetas_nombre ON carpetas (COALESCE(padre_id, 0), lower(btrim(nombre)));

CREATE TABLE documentos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    carpeta_id BIGINT REFERENCES carpetas (id) ON DELETE SET NULL,   -- NULL: en el inicio
    titulo TEXT NOT NULL CHECK (length(btrim(titulo)) BETWEEN 3 AND 150),
    descripcion TEXT NOT NULL DEFAULT '' CHECK (length(descripcion) <= 500),
    creado_por BIGINT NOT NULL,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_por BIGINT NOT NULL,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    eliminado_por BIGINT,
    eliminado_en TIMESTAMPTZ,                                         -- no NULL: está en la papelera
    CHECK ((eliminado_en IS NULL) = (eliminado_por IS NULL))
);
CREATE INDEX ix_documentos_carpeta ON documentos (carpeta_id) WHERE eliminado_en IS NULL;
CREATE INDEX ix_documentos_eliminado ON documentos (eliminado_en) WHERE eliminado_en IS NOT NULL;

-- Cada PDF subido. La versión vigente de un documento es la que no tiene reemplazada_en.
CREATE TABLE versiones (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    documento_id BIGINT NOT NULL REFERENCES documentos (id) ON DELETE CASCADE,
    contenido BYTEA NOT NULL,
    nombre_archivo TEXT NOT NULL CHECK (length(nombre_archivo) BETWEEN 1 AND 200),
    tamano INTEGER NOT NULL CHECK (tamano > 0),
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
    subida_por BIGINT NOT NULL,
    subida_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    reemplazada_por BIGINT,
    reemplazada_en TIMESTAMPTZ,                                       -- no NULL: versión anterior, en la papelera
    CHECK ((reemplazada_en IS NULL) = (reemplazada_por IS NULL))
);
CREATE UNIQUE INDEX ux_versiones_vigente ON versiones (documento_id) WHERE reemplazada_en IS NULL;
CREATE INDEX ix_versiones_reemplazada ON versiones (reemplazada_en) WHERE reemplazada_en IS NOT NULL;
CREATE INDEX ix_versiones_subida_por ON versiones (subida_por);

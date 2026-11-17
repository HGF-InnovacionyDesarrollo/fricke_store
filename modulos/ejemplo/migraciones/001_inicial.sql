-- Esquema inicial del módulo de ejemplo (se crea dentro del esquema m_ejemplo, con el rol del módulo).
-- Una migración aplicada NO se edita: los cambios van en 002_*.sql. Sin BEGIN/COMMIT: el portal ya usa una transacción.
-- Las personas se referencian por usuarios.id del portal (nunca el RUT). Fechas en TIMESTAMPTZ.
CREATE TABLE avisos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    autor_id BIGINT NOT NULL,                 -- usuarios.id del portal (otro esquema: sin FK)
    titulo TEXT NOT NULL CHECK (length(titulo) BETWEEN 3 AND 80),
    texto TEXT NOT NULL CHECK (length(texto) BETWEEN 3 AND 1000),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_avisos_autor ON avisos (autor_id);
CREATE INDEX ix_avisos_creado ON avisos (creado_en);

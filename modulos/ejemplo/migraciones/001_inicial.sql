-- Esquema inicial del módulo de ejemplo. Una migración aplicada NO se edita: los cambios van en 002_*.sql.
-- Las fechas se guardan en UTC ISO-8601; las personas se referencian por usuarios.id del portal (nunca el RUT).
CREATE TABLE avisos (
    id INTEGER PRIMARY KEY,
    autor_id INTEGER NOT NULL,          -- usuarios.id del portal
    titulo TEXT NOT NULL,
    texto TEXT NOT NULL,
    creado_en TEXT NOT NULL
);
CREATE INDEX ix_avisos_autor ON avisos(autor_id);
CREATE INDEX ix_avisos_creado ON avisos(creado_en);

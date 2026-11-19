-- La regla de los módulos pide no usar columnas BOOLEAN (el portal guarda sí/no como número 0/1).
-- sensores.activo nació BOOLEAN en 001 (que ya está aplicada y no se edita): aquí pasa a SMALLINT 0/1.
ALTER TABLE sensores ALTER COLUMN activo DROP DEFAULT;
ALTER TABLE sensores ALTER COLUMN activo TYPE SMALLINT USING (CASE WHEN activo THEN 1 ELSE 0 END);
ALTER TABLE sensores ALTER COLUMN activo SET DEFAULT 1;
ALTER TABLE sensores ADD CONSTRAINT ck_sensores_activo CHECK (activo IN (0, 1));

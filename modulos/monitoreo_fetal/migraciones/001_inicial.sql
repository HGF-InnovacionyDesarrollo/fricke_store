-- Esquema inicial del módulo Monitoreo fetal (se crea dentro del esquema m_monitoreo_fetal, con el rol del módulo).
-- Una migración aplicada NO se edita: los cambios van en 002_*.sql. Sin BEGIN/COMMIT: el portal ya usa una transacción.
-- Las personas se referencian por usuarios.id del portal (nunca el RUT). Fechas en TIMESTAMPTZ.
CREATE TABLE simulaciones (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    autor_id BIGINT NOT NULL,                 -- usuarios.id del portal (otro esquema: sin FK)
    titulo TEXT NOT NULL CHECK (length(titulo) BETWEEN 3 AND 100),
    escenario TEXT NOT NULL CHECK (escenario IN ('normal_reactivo', 'taquisistolia_cat2', 'variables_recurrentes_cat2', 'patologico_cat3', 'personalizado')),
    edad_gestacional_sem INTEGER NOT NULL CHECK (edad_gestacional_sem BETWEEN 24 AND 43),
    linea_base_lpm INTEGER NOT NULL CHECK (linea_base_lpm BETWEEN 50 AND 220),
    variabilidad_lpm NUMERIC(4,1) NOT NULL CHECK (variabilidad_lpm BETWEEN 0 AND 60),
    categoria_nichd TEXT NOT NULL CHECK (categoria_nichd IN ('ausente', 'minima', 'moderada', 'marcada')),
    num_aceleraciones INTEGER NOT NULL CHECK (num_aceleraciones BETWEEN 0 AND 40),
    num_desaceleraciones INTEGER NOT NULL CHECK (num_desaceleraciones BETWEEN 0 AND 40),
    tipo_desaceleracion TEXT NOT NULL CHECK (tipo_desaceleracion IN ('ninguna', 'precoz', 'variable', 'tardia', 'prolongada')),
    duracion_max_decel_s INTEGER NOT NULL CHECK (duracion_max_decel_s BETWEEN 0 AND 600),
    contracciones_10min NUMERIC(3,1) NOT NULL CHECK (contracciones_10min BETWEEN 0 AND 15),
    patron_sinusoidal BOOLEAN NOT NULL DEFAULT FALSE,
    categoria_figo TEXT NOT NULL CHECK (categoria_figo IN ('I', 'II', 'III')),
    categoria_acog TEXT NOT NULL CHECK (categoria_acog IN ('I', 'II', 'III')),
    riesgo_cat_ii TEXT NOT NULL CHECK (riesgo_cat_ii IN ('no_aplica', 'con_rasgos_protectores', 'intermedio', 'alto')),
    hipoxia_tipificada TEXT NOT NULL CHECK (hipoxia_tipificada IN ('sin_hipoxia', 'aguda', 'subaguda', 'progresiva', 'cronica')),
    resumen_conducta TEXT NOT NULL CHECK (length(resumen_conducta) BETWEEN 10 AND 2000),
    nota_docente TEXT NOT NULL DEFAULT '' CHECK (length(nota_docente) <= 600),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_simulaciones_autor ON simulaciones (autor_id);
CREATE INDEX ix_simulaciones_creado ON simulaciones (creado_en);

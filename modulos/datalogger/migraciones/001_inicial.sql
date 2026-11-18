-- Esquema inicial de Data+ (se crea dentro de m_datalogger, con el rol del módulo).
-- Una migración aplicada NO se edita: los cambios van en 002_*.sql. Sin BEGIN/COMMIT: el portal ya usa una transacción.
-- Las personas se referencian por usuarios.id del portal (nunca el RUT). Fechas en TIMESTAMPTZ (UTC).

-- Rangos de cada tipo de almacenamiento, según los protocolos del hospital (los mismos que usa el firmware).
-- Verde: dentro de [verde_min, verde_max]. Alarma: bajo alarma_min o sobre alarma_max. Entre ambos: atención.
CREATE TABLE perfiles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    clave TEXT NOT NULL UNIQUE CHECK (clave ~ '^[A-Z]{2,10}$'),
    nombre TEXT NOT NULL UNIQUE CHECK (length(nombre) BETWEEN 3 AND 60),
    referencia TEXT NOT NULL CHECK (length(referencia) BETWEEN 3 AND 120),
    t_verde_min NUMERIC(5,1), t_verde_max NUMERIC(5,1),
    t_alarma_min NUMERIC(5,1), t_alarma_max NUMERIC(5,1),
    h_verde_min NUMERIC(5,1), h_verde_max NUMERIC(5,1),
    h_alarma_min NUMERIC(5,1), h_alarma_max NUMERIC(5,1)
);
INSERT INTO perfiles (clave, nombre, referencia, t_verde_min, t_verde_max, t_alarma_min, t_alarma_max,
                      h_verde_min, h_verde_max, h_alarma_min, h_alarma_max) VALUES
    ('MED', 'Medicamentos', 'Protocolo APF 1.5', 16, 24, 15, 30, NULL, 55, NULL, 60),
    ('EST', 'Material estéril', 'Protocolo APE 1.4', 19, 23, 18, 24, 33, 47, 30, 50);

-- Cada data logger (unidad central). El código es la etiqueta (MTH-01); la serie identifica la placa física.
CREATE TABLE equipos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo TEXT NOT NULL UNIQUE CHECK (codigo ~ '^[A-Za-z0-9_-]{2,16}$'),
    serie TEXT CHECK (serie ~ '^[0-9A-F]{8,32}$'),
    firmware TEXT CHECK (length(firmware) <= 20),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE sensores (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ieee TEXT NOT NULL UNIQUE CHECK (ieee ~ '^[0-9A-F]{16}$'),
    equipo_id BIGINT NOT NULL REFERENCES equipos (id),
    numero INTEGER CHECK (numero BETWEEN 1 AND 99),
    nombre TEXT NOT NULL CHECK (length(nombre) BETWEEN 1 AND 40),       -- el que trae el equipo
    perfil_id BIGINT REFERENCES perfiles (id),
    ubicacion TEXT NOT NULL DEFAULT '' CHECK (length(ubicacion) <= 80),  -- la escribe el módulo
    activo BOOLEAN NOT NULL DEFAULT TRUE,                                 -- FALSE: fuera de servicio
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_sensores_equipo ON sensores (equipo_id);

-- Quién importó qué y con qué resultado (la persona por usuarios.id).
CREATE TABLE importaciones (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id BIGINT NOT NULL,                     -- usuarios.id del portal (otro esquema: sin FK)
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    archivos INTEGER NOT NULL CHECK (archivos >= 0),
    lecturas_nuevas INTEGER NOT NULL DEFAULT 0,
    lecturas_repetidas INTEGER NOT NULL DEFAULT 0,
    eventos_nuevos INTEGER NOT NULL DEFAULT 0,
    filas_rechazadas INTEGER NOT NULL DEFAULT 0,
    firmas TEXT NOT NULL DEFAULT 'sin_verificar' CHECK (firmas IN ('sin_verificar', 'correctas', 'con_problemas')),
    problemas_firma INTEGER NOT NULL DEFAULT 0,
    desde TIMESTAMPTZ,
    hasta TIMESTAMPTZ
);
CREATE INDEX ix_importaciones_usuario ON importaciones (usuario_id);
CREATE INDEX ix_importaciones_creado ON importaciones (creado_en);

-- Una fila cada 5 min por sensor. Los valores ya traen aplicada la corrección de calibración (corr_t, corr_h).
CREATE TABLE lecturas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sensor_id BIGINT NOT NULL REFERENCES sensores (id),
    fecha TIMESTAMPTZ NOT NULL,
    temperatura NUMERIC(5,1) CHECK (temperatura BETWEEN -80 AND 100),
    humedad NUMERIC(5,1) CHECK (humedad BETWEEN 0 AND 100),
    bateria SMALLINT CHECK (bateria BETWEEN 0 AND 100),
    hora_lectura TIMESTAMPTZ,
    corr_t NUMERIC(4,1),
    corr_h NUMERIC(4,1),
    firma TEXT CHECK (firma ~ '^[0-9a-f]{16}$'),
    importacion_id BIGINT NOT NULL REFERENCES importaciones (id),
    UNIQUE (sensor_id, fecha)
);
CREATE INDEX ix_lecturas_fecha ON lecturas (fecha);
CREATE INDEX ix_lecturas_importacion ON lecturas (importacion_id);

-- Registro de eventos del equipo (arranques, alarmas, cortes de luz, SD, calibración...).
CREATE TABLE eventos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    equipo_id BIGINT NOT NULL REFERENCES equipos (id),
    fecha TIMESTAMPTZ NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo ~ '^[A-Z0-9_]{2,40}$'),
    detalle TEXT NOT NULL DEFAULT '' CHECK (length(detalle) <= 300),
    firma TEXT CHECK (firma ~ '^[0-9a-f]{16}$'),
    importacion_id BIGINT NOT NULL REFERENCES importaciones (id),
    UNIQUE (equipo_id, fecha, tipo, detalle)
);
CREATE INDEX ix_eventos_fecha ON eventos (fecha);
CREATE INDEX ix_eventos_importacion ON eventos (importacion_id);

-- Períodos fuera del rango de alarma, calculados desde las lecturas, y su revisión.
CREATE TABLE excursiones (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sensor_id BIGINT NOT NULL REFERENCES sensores (id),
    variable TEXT NOT NULL CHECK (variable IN ('temperatura', 'humedad')),
    sentido TEXT NOT NULL CHECK (sentido IN ('alta', 'baja')),
    inicio TIMESTAMPTZ NOT NULL,
    fin TIMESTAMPTZ,                                -- NULL: sigue fuera de rango en el último dato
    extremo NUMERIC(5,1) NOT NULL,
    limite NUMERIC(5,1) NOT NULL,
    revisada_por BIGINT,                            -- usuarios.id del portal
    revisada_en TIMESTAMPTZ,
    accion TEXT CHECK (length(accion) BETWEEN 3 AND 500),
    UNIQUE (sensor_id, variable, inicio),
    CHECK ((revisada_por IS NULL) = (revisada_en IS NULL))
);
CREATE INDEX ix_excursiones_revisada_por ON excursiones (revisada_por);
CREATE INDEX ix_excursiones_pendientes ON excursiones (inicio) WHERE revisada_por IS NULL;

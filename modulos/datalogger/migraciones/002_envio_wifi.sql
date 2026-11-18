-- Envío por WiFi (firmware 2.1): cada minuto el equipo manda el último valor de cada sensor.
-- Son lecturas "en vivo": sirven para ver el estado al momento. El registro oficial sigue siendo el de la SD
-- (tabla lecturas, con firmas), que se importa como antes.
CREATE TABLE lecturas_wifi (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sensor_id BIGINT NOT NULL REFERENCES sensores (id),
    fecha TIMESTAMPTZ NOT NULL,                       -- hora del reporte del sensor (hora del equipo - edad)
    temperatura NUMERIC(5,1) CHECK (temperatura BETWEEN -80 AND 100),
    humedad NUMERIC(5,1) CHECK (humedad BETWEEN 0 AND 100),
    bateria SMALLINT CHECK (bateria BETWEEN 0 AND 100),
    recibido_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (sensor_id, fecha)
);
CREATE INDEX ix_lecturas_wifi_fecha ON lecturas_wifi (fecha);

-- Estado del último envío de cada equipo.
ALTER TABLE equipos ADD COLUMN wifi_ultimo_envio TIMESTAMPTZ;
ALTER TABLE equipos ADD COLUMN wifi_rssi SMALLINT;
ALTER TABLE equipos ADD COLUMN wifi_envios_ok INTEGER;
ALTER TABLE equipos ADD COLUMN wifi_envios_falla INTEGER;

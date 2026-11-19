-- Estado de la tarjeta SD que informa cada equipo en su envío WiFi (firmware 2.2). Así F+data avisa que la SD
-- no está grabando sin esperar a que alguien la importe. NULL = el equipo no lo informa (firmware anterior).
ALTER TABLE equipos ADD COLUMN sd_ok SMALLINT CHECK (sd_ok IN (0, 1));
ALTER TABLE equipos ADD COLUMN sd_fuera_desde TIMESTAMPTZ;           -- desde cuándo no graba (NULL si graba)
ALTER TABLE equipos ADD COLUMN sd_pendientes INTEGER CHECK (sd_pendientes >= 0);  -- filas esperando en la flash

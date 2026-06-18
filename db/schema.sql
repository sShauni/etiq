-- Schema do banco PostgreSQL central.
-- Rodar uma vez no servidor antes de ligar os Pis.

CREATE TABLE IF NOT EXISTS contagem (
    id          SERIAL PRIMARY KEY,
    ciclo_uid   TEXT        NOT NULL UNIQUE,
    maquina     TEXT        NOT NULL,
    sku         TEXT        NOT NULL,
    qtd         INTEGER     NOT NULL,
    data_hora   TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_contagem_data_hora ON contagem (data_hora);
CREATE INDEX IF NOT EXISTS idx_contagem_maquina   ON contagem (maquina);

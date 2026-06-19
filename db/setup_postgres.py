"""
Inicializa o schema no PostgreSQL central.
Rodar uma única vez no servidor antes de ligar os Pis.

Uso:
    python db/setup_postgres.py
    python db/setup_postgres.py --host 192.168.1.10 --user pi --password SENHA
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2
from config.settings import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS contagem (
    id          SERIAL PRIMARY KEY,
    ciclo_uid   TEXT                        NOT NULL UNIQUE,
    maquina     TEXT                        NOT NULL,
    sku         TEXT                        NOT NULL,
    qtd         INTEGER                     NOT NULL,
    data_hora   TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    operador    INTEGER
);

ALTER TABLE contagem ADD COLUMN IF NOT EXISTS operador INTEGER;

CREATE INDEX IF NOT EXISTS idx_contagem_data_hora ON contagem (data_hora);
CREATE INDEX IF NOT EXISTS idx_contagem_maquina   ON contagem (maquina);
CREATE INDEX IF NOT EXISTS idx_contagem_operador  ON contagem (operador);
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Inicializa schema no PostgreSQL")
    parser.add_argument("--host",     default=settings.pg_host)
    parser.add_argument("--port",     default=settings.pg_port, type=int)
    parser.add_argument("--dbname",   default=settings.pg_dbname)
    parser.add_argument("--user",     default=settings.pg_user)
    parser.add_argument("--password", default=settings.pg_password)
    args = parser.parse_args()

    print(f"\nConectando em {args.user}@{args.host}:{args.port}/{args.dbname} ...")

    try:
        conn = psycopg2.connect(
            host=args.host,
            port=args.port,
            dbname=args.dbname,
            user=args.user,
            password=args.password,
            connect_timeout=10,
        )
    except psycopg2.OperationalError as e:
        print(f"\n✗ Falha na conexão: {e}")
        sys.exit(1)

    with conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
    conn.close()

    print("✓ Schema criado/verificado com sucesso.")
    print("  Tabela: contagem")
    print("  Índices: idx_contagem_data_hora, idx_contagem_maquina\n")


if __name__ == "__main__":
    main()

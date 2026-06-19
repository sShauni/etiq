"""
Sincronização do SQLite local com o PostgreSQL central.
Executa em loop contínuo; envia apenas eventos ainda não sincronizados.
Idempotente: INSERT ... ON CONFLICT DO NOTHING (ciclo_uid UNIQUE no Postgres).
"""

import os
import sys
import time
import logging
from pathlib import Path

# No Windows com PostgreSQL em locale Portuguese_Brazil.1252, o libpq gera mensagens
# de erro em cp1252. LANG=C força mensagens em ASCII para evitar UnicodeDecodeError.
os.environ.setdefault('LANG', 'C')
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import psycopg2

from config.settings import settings
from core.sku_mapper import SKUMapper
from data.sqlite_logger import SQLiteProductionLogger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [sync] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

INSERT_SQL = """
    INSERT INTO contagem (ciclo_uid, maquina, sku, qtd, data_hora, operador)
    VALUES (%(ciclo_uid)s, %(maquina)s, %(sku)s, %(qtd)s, %(data_hora)s, %(operador)s)
    ON CONFLICT (ciclo_uid) DO NOTHING
"""


def _pg_connect() -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=settings.pg_host,
        port=settings.pg_port,
        dbname=settings.pg_dbname,
        user=settings.pg_user,
        password=settings.pg_password,
        connect_timeout=10,
    )


def sync_once(local: SQLiteProductionLogger) -> None:
    """Envia um lote de eventos pendentes ao Postgres; marca como sincronizados."""
    pending = local.get_pending_sync()
    if not pending:
        return

    log.info(f"{len(pending)} evento(s) pendente(s)")

    try:
        with _pg_connect() as pg:
            with pg.cursor() as cur:
                cur.executemany(INSERT_SQL, pending)
            pg.commit()

        ids = [r["id"] for r in pending]
        local.mark_synced(ids)
        log.info(f"{len(ids)} evento(s) sincronizado(s)")

    except psycopg2.OperationalError as e:
        log.warning(f"Sem conexão com o servidor: {e}")
    except Exception as e:
        log.error(f"Erro inesperado na sincronização: {e}")


def run(interval_seconds: int = 60) -> None:
    """Loop principal de sincronização."""
    mapper = SKUMapper(settings.sku_file_path)
    local = SQLiteProductionLogger(mapper)

    log.info(
        f"Sincronizador iniciado — máquina={settings.machine_id}, "
        f"intervalo={interval_seconds}s, destino={settings.pg_host}"
    )

    while True:
        sync_once(local)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run()

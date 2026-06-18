"""
Testa a conexão com o PostgreSQL e dispara uma sincronização imediata.
Útil para verificar se o Pi consegue falar com o servidor antes de ligar o loop.

Uso:
    python db/test_sync.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2
from config.settings import settings
from core.sku_mapper import SKUMapper
from data.sqlite_logger import SQLiteProductionLogger
from data.sync import sync_once


def test_connection() -> bool:
    print(f"\n1. Testando conexão com PostgreSQL...")
    print(f"   Host:   {settings.pg_host}:{settings.pg_port}")
    print(f"   Banco:  {settings.pg_dbname}")
    print(f"   Usuário: {settings.pg_user}")

    try:
        conn = psycopg2.connect(
            host=settings.pg_host,
            port=settings.pg_port,
            dbname=settings.pg_dbname,
            user=settings.pg_user,
            password=settings.pg_password,
            connect_timeout=10,
        )

        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]

        conn.close()
        print(f"   ✓ Conectado: {version[:50]}...")
        return True

    except psycopg2.OperationalError as e:
        print(f"   ✗ Falha na conexão: {e}")
        return False


def test_table_exists() -> bool:
    print(f"\n2. Verificando tabela 'contagem'...")

    try:
        conn = psycopg2.connect(
            host=settings.pg_host,
            port=settings.pg_port,
            dbname=settings.pg_dbname,
            user=settings.pg_user,
            password=settings.pg_password,
            connect_timeout=10,
        )

        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_name = 'contagem'
            """)
            exists = cur.fetchone()[0] == 1

            if exists:
                cur.execute("SELECT COUNT(*) FROM contagem")
                total = cur.fetchone()[0]
                print(f"   ✓ Tabela existe — {total} registro(s) no servidor")
            else:
                print("   ✗ Tabela 'contagem' não encontrada.")
                print("     Execute: python db/setup_postgres.py")

        conn.close()
        return exists

    except Exception as e:
        print(f"   ✗ Erro: {e}")
        return False


def test_sync() -> None:
    print(f"\n3. Sincronização manual...")

    mapper = SKUMapper(settings.sku_file_path)
    local = SQLiteProductionLogger(mapper)

    pending = local.get_pending_sync()
    print(f"   Eventos pendentes no SQLite: {len(pending)}")

    if not pending:
        print("   (nada a sincronizar)")
        return

    sync_once(local)

    still_pending = local.get_pending_sync()
    synced = len(pending) - len(still_pending)
    print(f"   ✓ Sincronizados agora: {synced}")
    print(f"   Ainda pendentes: {len(still_pending)}")


def main() -> None:
    ok_conn = test_connection()
    if not ok_conn:
        sys.exit(1)

    ok_table = test_table_exists()
    if not ok_table:
        sys.exit(1)

    test_sync()
    print()


if __name__ == "__main__":
    main()

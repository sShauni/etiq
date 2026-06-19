"""
API REST para exposição dos dados de produção ao ERP.
O ERP faz pull periódico passando o último id recebido como cursor.

Uso:
    python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

Configuração via variáveis de ambiente (ou editar os defaults abaixo):
    PG_HOST, PG_PORT, PG_DBNAME, PG_USER, PG_PASSWORD

Endpoint principal:
    GET /producao?since_id=0   → retorna registros com id > since_id
"""

import os

os.environ.setdefault('LANG', 'C')

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, Query

PG_HOST     = os.getenv('PG_HOST',     'localhost')
PG_PORT     = int(os.getenv('PG_PORT', '5432'))
PG_DBNAME   = os.getenv('PG_DBNAME',  'producao')
PG_USER     = os.getenv('PG_USER',     'producao_pi')
PG_PASSWORD = os.getenv('PG_PASSWORD', '25565')

app = FastAPI(
    title="Etiq Produção API",
    description="Exposição de dados de produção para o ERP.",
    version="1.0.0",
)


def _pg_connect():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DBNAME,
        user=PG_USER,
        password=PG_PASSWORD,
        connect_timeout=10,
    )


@app.get("/producao")
def get_producao(
    since_id: int = Query(0, description="Retorna apenas registros com id maior que este valor"),
    limit: int = Query(1000, le=5000, description="Máximo de registros por chamada"),
):
    """
    Retorna registros de produção novos desde o último pull.

    O ERP deve armazenar o maior `id` recebido e passá-lo como `since_id`
    na próxima chamada. Repetir até a lista retornar vazia.
    """
    with _pg_connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, ciclo_uid, maquina, sku, qtd, data_hora
                FROM contagem
                WHERE id > %s
                ORDER BY id ASC
                LIMIT %s
                """,
                (since_id, limit),
            )
            rows = cur.fetchall()

    return [dict(r) for r in rows]


@app.get("/health")
def health():
    """Verifica se a API está no ar."""
    return {"status": "ok"}

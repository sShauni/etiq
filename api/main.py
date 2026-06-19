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
from typing import Optional

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
    operador: Optional[int] = Query(None, description="Filtra por chave do cartão do operador"),
    data_de: Optional[str] = Query(None, description="Início do período (ISO 8601: 2026-06-19T06:00:00)"),
    data_ate: Optional[str] = Query(None, description="Fim do período (ISO 8601: 2026-06-19T14:00:00)"),
):
    """
    Retorna registros de produção novos desde o último pull.

    O ERP deve armazenar o maior `id` recebido e passá-lo como `since_id`
    na próxima chamada. Repetir até a lista retornar vazia.

    Filtros opcionais: operador (chave do cartão), data_de e data_ate (para consultas por turno).
    """
    filters = ["id > %(since_id)s"]
    params: dict = {"since_id": since_id, "limit": limit}

    if operador is not None:
        filters.append("operador = %(operador)s")
        params["operador"] = operador

    if data_de is not None:
        filters.append("data_hora >= %(data_de)s")
        params["data_de"] = data_de

    if data_ate is not None:
        filters.append("data_hora <= %(data_ate)s")
        params["data_ate"] = data_ate

    where = " AND ".join(filters)

    with _pg_connect() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT id, ciclo_uid, maquina, sku, qtd, data_hora, operador
                FROM contagem
                WHERE {where}
                ORDER BY id ASC
                LIMIT %(limit)s
                """,
                params,
            )
            rows = cur.fetchall()

    return [dict(r) for r in rows]


@app.get("/health")
def health():
    """Verifica se a API está no ar."""
    return {"status": "ok"}

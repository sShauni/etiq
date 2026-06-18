"""
Logger de produção offline-first usando SQLite local.
Substitui o logger CSV; mesma interface pública + métodos de sincronização.
"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from config.settings import settings
from core.sku_mapper import SKUMapper


class SQLiteProductionLogger:
    """Grava cada ciclo de produção como um evento imutável no SQLite local."""

    def __init__(
        self,
        sku_mapper: SKUMapper,
        db_path: Path | None = None,
        machine_id: str | None = None,
    ):
        self.sku_mapper = sku_mapper
        self.machine_id = machine_id or settings.machine_id
        self.db_path = Path(db_path or settings.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        print(f"✓ SQLite logger inicializado: {self.db_path}")

    # ------------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contagem (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ciclo_uid   TEXT    NOT NULL UNIQUE,
                    maquina     TEXT    NOT NULL,
                    sku         TEXT    NOT NULL,
                    qtd         INTEGER NOT NULL,
                    data_hora   TIMESTAMP NOT NULL,
                    sincronizado INTEGER NOT NULL DEFAULT 0
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_data_hora    ON contagem (data_hora)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sincronizado ON contagem (sincronizado)"
            )

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    # ------------------------------------------------------------------
    # Interface pública (compatível com ProductionLogger)
    # ------------------------------------------------------------------

    def log_production(self, codigo: float, automatica: bool = False) -> bool:
        """Registra um ciclo de produção como evento novo."""
        sku = self.sku_mapper.get_sku(codigo)
        if not sku:
            print(f"⚠ Código {codigo} não encontrado na tabela de SKUs")
            return False

        ciclo_uid = str(uuid.uuid4())
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with self._conn() as conn:
                conn.execute(
                    """INSERT OR IGNORE INTO contagem
                       (ciclo_uid, maquina, sku, qtd, data_hora)
                       VALUES (?, ?, ?, ?, ?)""",
                    (ciclo_uid, self.machine_id, sku, 1, data_hora),
                )
            modo = "automática" if automatica else "manual"
            print(f"✓ Produção registrada ({modo}): SKU {sku}")
            return True
        except Exception as e:
            print(f"✗ Erro ao registrar produção: {e}")
            return False

    def log_multiple_productions(self, codigos: list, automatica: bool = False) -> int:
        """Registra múltiplos ciclos; retorna quantos foram gravados com sucesso."""
        return sum(1 for c in codigos if self.log_production(c, automatica))

    def get_today_summary(self) -> Dict[str, int]:
        """Retorna {sku: total_do_dia} para a máquina atual."""
        today = datetime.now().strftime("%Y-%m-%d")
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT sku, SUM(qtd)
                   FROM contagem
                   WHERE maquina = ? AND data_hora >= ?
                   GROUP BY sku""",
                (self.machine_id, today),
            ).fetchall()
        return {sku: qty for sku, qty in rows}

    def get_total_today(self) -> int:
        """Total de peças produzidas hoje."""
        return sum(self.get_today_summary().values())

    # ------------------------------------------------------------------
    # Sincronização com Postgres (usado pelo sync layer)
    # ------------------------------------------------------------------

    def get_pending_sync(self) -> List[dict]:
        """Retorna eventos ainda não enviados ao Postgres central."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT id, ciclo_uid, maquina, sku, qtd, data_hora
                   FROM contagem
                   WHERE sincronizado = 0
                   ORDER BY id""",
            ).fetchall()
        cols = ("id", "ciclo_uid", "maquina", "sku", "qtd", "data_hora")
        return [dict(zip(cols, r)) for r in rows]

    def mark_synced(self, ids: List[int]) -> None:
        """Marca eventos como sincronizados após envio bem-sucedido ao Postgres."""
        if not ids:
            return
        placeholders = ",".join("?" * len(ids))
        with self._conn() as conn:
            conn.execute(
                f"UPDATE contagem SET sincronizado = 1 WHERE id IN ({placeholders})",
                ids,
            )


if __name__ == "__main__":
    from core.sku_mapper import SKUMapper

    mapper = SKUMapper(settings.sku_file_path)
    logger = SQLiteProductionLogger(mapper)

    print("\nTestando log de produção...")
    logger.log_production(111.1)
    logger.log_multiple_productions([111.1, 112.1], automatica=True)

    summary = logger.get_today_summary()
    print(f"\nResumo de hoje: {summary}")
    print(f"Total: {logger.get_total_today()} peças")

    pending = logger.get_pending_sync()
    print(f"\nEventos pendentes de sync: {len(pending)}")

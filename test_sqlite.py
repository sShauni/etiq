"""
Teste local do SQLiteProductionLogger — roda no Windows sem Excel nem Pi.
Cria o banco em ./test_producao.db e apaga ao final.
"""

import sys
import os
from pathlib import Path

# Permite importar os módulos do projeto sem instalar como pacote
sys.path.insert(0, os.path.dirname(__file__))

from data.sqlite_logger import SQLiteProductionLogger

DB_TEST = Path(__file__).parent / "test_producao.db"

# Mock mínimo do SKUMapper: dicionário estático no lugar do Excel
class FakeSKUMapper:
    _map = {111.1: "SKU-A", 112.1: "SKU-B", 121.1: "SKU-C"}

    def get_sku(self, codigo: float):
        return self._map.get(round(float(codigo), 1))


def sep(titulo: str) -> None:
    print(f"\n{'='*50}")
    print(f"  {titulo}")
    print('='*50)


def main() -> None:
    # Garante db limpo a cada execução
    DB_TEST.unlink(missing_ok=True)

    logger = SQLiteProductionLogger(
        sku_mapper=FakeSKUMapper(),
        db_path=DB_TEST,
        machine_id="TEST-WIN",
    )

    # ------------------------------------------------------------------
    sep("1. log_production — código válido")
    ok = logger.log_production(111.1)
    assert ok, "Deveria retornar True"

    sep("2. log_production — código inválido")
    ok = logger.log_production(999.9)
    assert not ok, "Deveria retornar False para código não mapeado"

    sep("3. log_multiple_productions")
    n = logger.log_multiple_productions([111.1, 112.1, 121.1], automatica=True)
    assert n == 3, f"Esperava 3, got {n}"

    sep("4. get_today_summary")
    summary = logger.get_today_summary()
    print(f"  Resumo: {summary}")
    assert summary.get("SKU-A") == 2, "SKU-A deveria ter 2 (1 + 1)"
    assert summary.get("SKU-B") == 1
    assert summary.get("SKU-C") == 1

    sep("5. get_total_today")
    total = logger.get_total_today()
    print(f"  Total: {total}")
    assert total == 4

    sep("6. get_pending_sync — todos pendentes")
    pending = logger.get_pending_sync()
    print(f"  Pendentes: {len(pending)}")
    for r in pending:
        print(f"    id={r['id']}  sku={r['sku']}  data_hora={r['data_hora']}")
    assert len(pending) == 4

    sep("7. mark_synced — marca os 2 primeiros")
    ids_batch = [pending[0]["id"], pending[1]["id"]]
    logger.mark_synced(ids_batch)
    still_pending = logger.get_pending_sync()
    print(f"  Ainda pendentes após sync parcial: {len(still_pending)}")
    assert len(still_pending) == 2

    sep("8. Idempotência — reinserir mesmo ciclo_uid")
    uid = pending[0]["ciclo_uid"]
    import sqlite3
    with sqlite3.connect(DB_TEST) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO contagem (ciclo_uid, maquina, sku, qtd, data_hora) VALUES (?, ?, ?, ?, ?)",
            (uid, "TEST-WIN", "SKU-A", 1, "2026-01-01 00:00:00"),
        )
    total_apos = logger.get_total_today()
    assert total_apos == 4, "Total não deve aumentar com ciclo_uid duplicado"
    print("  Reinserção ignorada corretamente.")

    # ------------------------------------------------------------------
    print(f"\n{'='*50}")
    print("  TODOS OS TESTES PASSARAM")
    print('='*50)

    DB_TEST.unlink(missing_ok=True)
    print(f"\nBanco de teste removido: {DB_TEST.name}\n")


if __name__ == "__main__":
    main()

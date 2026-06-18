# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos

```bash
# Rodar a aplicação completa (UI + logger)
python main.py

# Teste isolado do SQLite (sem Excel, sem impressora)
python test_sqlite.py

# Criar schema no PostgreSQL (rodar uma vez no servidor)
python db/setup_postgres.py

# Testar conexão com PostgreSQL e disparar sync manual
python db/test_sync.py

# Rodar sincronização contínua em paralelo ao app (Pi)
python data/sync.py
```

## Arquitetura

O sistema coleta produção de máquinas de chão de fábrica (Raspberry Pi Zero 2W) e expõe os dados para um ERP externo via API REST.

```
[Usuário/GPIO] → UI (Tkinter) → main.py → LabelPrinter → [impressora CUPS]
                                        ↓
                               SQLiteProductionLogger
                               (producao.db — offline-first)
                                        ↓ sync.py (loop paralelo)
                               PostgreSQL central
                                        ↓ (próxima etapa)
                               FastAPI REST ← ERP (MS SQL Server, pull)
```

### Configuração por máquina

`config/settings.py` é um singleton que carrega `config/machine_config.json` pelo **hostname** da máquina (ou variável de ambiente `MACHINE_ID`). Cada Pi tem sua entrada (`s01`–`s11`); em desenvolvimento Windows cai no bloco `"default"`. Para testar como uma máquina específica: `MACHINE_ID=s01 python main.py`.

### Cálculo do código de produto

`core/calculator.py` — fórmula: `código = altura_val + 10*(fio+1) + 100*(malha+1)`. Cada código numérico (ex: `120.1`) mapeia para um arquivo `.tspl` em `labels_dir` e para um SKU via `SKU.xlsx`. Quando duas alturas são selecionadas, cada uma gera um código individual e uma etiqueta separada.

### Fluxo de impressão → gravação

Em `main.py._on_print_request`:
1. `OutputCalculator.calculate_all_outputs` → lista de códigos
2. `LabelPrinter.get_label_info` — verifica se o `.tspl` existe; aborta se não
3. `LabelPrinter.print_multiple_labels` — com `test_mode: true` só loga `[TESTE]`, sem CUPS
4. `SQLiteProductionLogger.log_multiple_productions` — só chamado se `sucessos > 0`

### Modelo de dados (eventos, não totais)

Cada impressão = uma linha nova em `contagem`. Nunca atualizar linhas existentes.

```sql
contagem: id, ciclo_uid (UNIQUE), maquina, sku, qtd, data_hora (TIMESTAMP), sincronizado
```

`ciclo_uid` é UUID4 gerado no Pi. `INSERT OR IGNORE ON CONFLICT (ciclo_uid)` garante idempotência em reenvios após queda de rede.

### Sincronização SQLite → PostgreSQL

`data/sync.py` roda como processo separado (no Pi: systemd service). Busca linhas com `sincronizado=0`, faz `INSERT ... ON CONFLICT DO NOTHING` no Postgres, marca como sincronizadas. Se não tiver rede, apenas loga aviso e tenta no próximo ciclo — nada se perde.

### Setup do PostgreSQL (servidor — feito uma vez só)

O servidor não precisa de nenhuma alteração ao adicionar máquinas novas. Todas as máquinas usam o mesmo usuário PostgreSQL definido no bloco `"default"` de `machine_config.json`, herdado via merge para todos os blocos de máquina. O campo `maquina` nos registros diferencia a origem dos dados.

```sql
-- Rodar como superuser (postgres) uma única vez:
CREATE DATABASE producao;
CREATE USER alan WITH PASSWORD 'senha';
GRANT ALL PRIVILEGES ON DATABASE producao TO alan;
-- PostgreSQL 15+: conceder permissão no schema public
GRANT ALL ON SCHEMA public TO alan;
```

Em seguida criar a tabela:
```bash
python db/setup_postgres.py
```

**Adicionar nova máquina:** criar o bloco `"s13"` em `machine_config.json`, copiar o arquivo para o Pi e setar o hostname. Zero alteração no servidor.

**O usuário PostgreSQL é independente do usuário do SO do Pi** — pode ser qualquer nome (`alan`, `producao`, `pi_sync`). O que importa é consistência entre o servidor e o `pg_user` no `machine_config.json`.

## Testar no Windows

O bloco `"default"` em `machine_config.json` tem `test_mode: true`, `db_path: "producao.db"` (relativo à raiz do projeto) e `labels_dir: "beta/etiquetas"` (onde estão os `.tspl`). O banco SQLite é criado em `etiq/producao.db` automaticamente.

Para inspecionar o banco após uso: abrir `producao.db` no [DB Browser for SQLite](https://sqlitebrowser.org/) → aba "Navegar Dados".

## Estado da migração

| Camada | Status |
|---|---|
| SQLite local (`data/sqlite_logger.py`) | Implementado |
| Sync TCP com PostgreSQL (`data/sync.py`) | Implementado |
| Schema PostgreSQL (`db/schema.sql`, `db/setup_postgres.py`) | Implementado |
| API REST FastAPI | Próxima etapa |
| Integração ERP | Aguarda definição do fornecedor |

`data/samba_client.py` e `data/logger.py` (CSV) são legados — não são usados no novo fluxo.

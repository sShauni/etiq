# Integração ERP — API de Produção

Este documento descreve como o sistema ERP deve consumir a API REST de produção.

---

## Visão Geral

A API expõe os registros de produção coletados nas máquinas de chão de fábrica (Raspberry Pi). Cada registro representa uma impressão de etiqueta — ou seja, um lote produzido.

O modelo de integração é **pull periódico com cursor**: o ERP chama a API em intervalos regulares passando o último ID recebido. A API retorna apenas os registros novos desde essa chamada.

---

## Acesso

| Item | Valor |
|---|---|
| URL base | `http://192.168.0.250:8000` |
| Autenticação | Nenhuma (rede interna) |
| Formato | JSON |
| Protocolo | HTTP |

---

## Endpoints

### `GET /health`

Verifica se a API está no ar. Útil para monitoramento.

**Resposta:**
```json
{"status": "ok"}
```

---

### `GET /producao`

Retorna registros de produção. Todos os parâmetros são opcionais.

**Parâmetros:**

| Parâmetro | Tipo | Padrão | Descrição |
|---|---|---|---|
| `since_id` | inteiro | `0` | Retorna apenas registros com `id` maior que este valor |
| `limit` | inteiro | `1000` | Máximo de registros por chamada (limite: 5000) |
| `operador` | inteiro | — | Filtra por chave do cartão do operador |
| `data_de` | string ISO 8601 | — | Início do período (`2026-06-19T06:00:00`) |
| `data_ate` | string ISO 8601 | — | Fim do período (`2026-06-19T14:00:00`) |

**Resposta — lista de objetos JSON:**

```json
[
  {
    "id": 42,
    "ciclo_uid": "a3f1c2d4-...",
    "maquina": "s06",
    "sku": "ABC-123",
    "qtd": 1,
    "data_hora": "2026-06-19T10:30:00",
    "operador": 98765
  }
]
```

**Descrição dos campos:**

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | inteiro | Identificador sequencial — usar como cursor no próximo pull |
| `ciclo_uid` | string (UUID) | Identificador único do ciclo de produção — idempotente |
| `maquina` | string | Código da máquina (ex: `s01` a `s11`) |
| `sku` | string | Código do produto |
| `qtd` | inteiro | Quantidade produzida no ciclo |
| `data_hora` | datetime (UTC) | Data e hora da produção |
| `operador` | inteiro ou null | Chave do cartão magnético do operador — ver seção abaixo |

---

## Padrão de Pull Periódico

O ERP deve armazenar o maior `id` recebido e usá-lo como `since_id` na próxima chamada.

```
1ª chamada (inicialização):
  GET /producao?since_id=0
  → recebe registros com id 1 a 47
  → ERP salva: last_id = 47

2ª chamada (5 minutos depois):
  GET /producao?since_id=47
  → recebe apenas o que entrou após o id 47
  → se retornar [] não há novidades

3ª chamada:
  GET /producao?since_id=<último id recebido>
  → repete indefinidamente
```

**Regras importantes:**
- O campo `ciclo_uid` é único — em caso de reenvio por falha de rede, o mesmo registro não será duplicado
- Ordenação sempre crescente por `id`
- Quando a resposta vier vazia (`[]`), não há registros novos

---

## Consultas por Turno

Use `data_de` e `data_ate` para restringir o período. Exemplo para o turno da manhã (06h–14h):

```
GET /producao?data_de=2026-06-19T06:00:00&data_ate=2026-06-19T14:00:00
```

Combinado com `since_id` para pull incremental dentro do turno:

```
GET /producao?since_id=100&data_de=2026-06-19T06:00:00&data_ate=2026-06-19T14:00:00
```

---

## Campo Operador

O campo `operador` contém a **chave numérica do cartão magnético** do operador, não o nome. O cruzamento chave → nome deve ser feito pelo ERP usando a tabela de operadores fornecida separadamente.

- Valor `null`: produção registrada sem operador identificado
- Valor numérico: chave do cartão a ser cruzada com a tabela de operadores

---

## Exemplos de Requisição

**Todos os registros:**
```
GET http://192.168.0.250:8000/producao?since_id=0
```

**Apenas novos desde o id 500:**
```
GET http://192.168.0.250:8000/producao?since_id=500
```

**Produção do turno da tarde de um dia específico:**
```
GET http://192.168.0.250:8000/producao?data_de=2026-06-19T14:00:00&data_ate=2026-06-19T22:00:00
```

**Produção de um operador específico:**
```
GET http://192.168.0.250:8000/producao?operador=98765
```

---

## Documentação Interativa

Com a API no ar, acesse pelo navegador:

```
http://192.168.0.250:8000/docs
```

A interface permite testar todos os endpoints diretamente, sem nenhuma ferramenta adicional.

# pagamentos-api

API de pagamentos de brinquedo usada no hands-on de code review da turma IAPD-26T3 (IA Aplicada à Produtividade no Desenvolvimento, semana 3). Python 3.10+, só biblioteca padrão e `pytest`.

## Onde este repositório entra na Semana 3

| Aula | Uso | Material |
|---|---|---|
| Aula 01 (Ter 03/11) | Atividade 1.1: escrever o steering do repo a partir deste README. Atividade 1.3 + Disputa 1: a skill v0 de code review revisa a branch `main` (14 bugs plantados) e o relatório é pontuado | [2026-11-03 - Aula 01 - Steering e skill](https://github.com/SENAI-IA/iapd-26t3-materiais/tree/main/2026-11-03-iapd-26t3-s03-aula-01-steering-e-skill) |
| Aula 02 (Qua 04/11) | Atividade 2.2 + Disputa 2: a suíte `review-*` com agente revisor roda de novo sobre a `main`; compara-se recall e falsos positivos com a v0 | [2026-11-04 - Aula 02 - Multiplas skills](https://github.com/SENAI-IA/iapd-26t3-materiais/tree/main/2026-11-04-iapd-26t3-s03-aula-02-multiplas-skills) |
| Aula 03 (Qui 05/11) | Torneio Red Team x Blue Team: cada equipe copia a branch `clean` para `iapd-26t3-eNN-torneio`, planta 5 bugs e o outro time caça com a própria suíte | [2026-11-05 - Aula 03 - Spec e o Torneio](https://github.com/SENAI-IA/iapd-26t3-materiais/tree/main/2026-11-05-iapd-26t3-s03-aula-03-spec-e-o-torneio) |

Branches: `main` (com os bugs plantados, usada nas Disputas 1 e 2) e `clean` (sem bugs, base do Torneio). O gabarito dos bugs fica com o professor até o fim de cada disputa.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install pytest
pytest -q
```

## Mapa do código

| Arquivo | Responsabilidade |
|---|---|
| `app/money.py` | conversão e arredondamento de dinheiro em centavos |
| `app/db.py` | conexão sqlite3, schema, consultas de leitura |
| `app/auth.py` | tokens de API, segredo e assinatura HMAC de webhooks |
| `app/payments.py` | criação e captura de pagamentos |
| `app/refunds.py` | reembolsos parciais e totais |
| `app/ledger.py` | saldo das contas, crédito, débito, extrato |
| `app/webhooks.py` | recebimento de eventos do adquirente |
| `app/api.py` | roteamento HTTP como funções puras |

## Gotchas do projeto (o que o revisor precisa saber)

1. **Dinheiro é `int` em centavos.** Nenhuma quantia passa por `float`. Conversão de string usa `Decimal` com arredondamento half-even. Taxas em basis points.
2. **sqlite3 puro, sem ORM.** Toda consulta usa placeholders `?`. Formatar SQL com f-string ou `%` é proibido, mesmo para valores "internos".
3. **Segredos comparados com `secrets.compare_digest` / `hmac.compare_digest`.** `==` em token ou assinatura é bug de segurança.
4. **Segredos vêm do ambiente** (`WEBHOOK_SECRET`). Não existe valor padrão no código.
5. **Timestamps em UTC com tzinfo**: `datetime.now(timezone.utc)`. `datetime.now()` sem argumento é bug.
6. **Webhooks são idempotentes**: o adquirente reenvia eventos; o mesmo `event_id` só é processado uma vez.
7. **Débito é um único `UPDATE ... WHERE balance_cents >= ?`.** Ler o saldo em Python e escrever de volta cria condição de corrida.
8. **Nunca registrar PAN completo ou token em log.** Só os 4 últimos dígitos.
9. **Erros são exceções tipadas.** Função que devolve `None` para sinalizar falha é bug de API.
10. **Paginação é 1-based**: `page=1` devolve os primeiros `page_size` registros.

## Branches

- `main`: código em revisão (o que a turma recebe).
- `clean`: referência. Fica com o professor até o fim da disputa.

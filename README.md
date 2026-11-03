# pagamentos-api

API de pagamentos de brinquedo usada no hands-on de code review da turma IAPD-26T3 (IA Aplicada à Produtividade no Desenvolvimento, semana 3). Python 3.10+, só biblioteca padrão e `pytest`.

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

import json

import pytest

from app.auth import generate_token, sign, verify_signature, verify_token
from app.ledger import InsufficientFunds, balance, credit, debit, statement
from app.payments import create_payment, get_payment
from app.webhooks import InvalidSignature, handle_webhook

SECRET = "s3gr3d0-de-teste"


def test_tokens():
    t = generate_token()
    assert verify_token(t, t)
    assert not verify_token(t + "x", t)


def test_assinatura():
    sig = sign(b"abc", SECRET)
    assert verify_signature(b"abc", sig, SECRET)
    assert not verify_signature(b"abd", sig, SECRET)


def test_credito_e_debito(conn):
    credit(conn, "alice", 500, "bonus")
    debit(conn, "alice", 1_500, "compra")
    assert balance(conn, "alice") == 9_000


def test_debito_sem_saldo(conn):
    with pytest.raises(InsufficientFunds):
        debit(conn, "alice", 999_999, "compra")


def test_statement(conn):
    credit(conn, "alice", 100, "x")
    st = statement(conn, ["alice", "merchant"])
    assert st["alice"]["balance_cents"] == 10_100
    assert len(st["alice"]["entries"]) == 1
    assert st["merchant"]["entries"] == []


def test_webhook_captura_e_credita(conn):
    pid = create_payment(conn, "c1", 700, "4111111111111111")
    payload = json.dumps({"id": "evt_1", "type": "payment.captured", "payment_id": pid}).encode()
    assert handle_webhook(conn, payload, sign(payload, SECRET), SECRET) == "processed"
    assert get_payment(conn, pid)["status"] == "captured"
    assert balance(conn, "merchant") == 700


def test_webhook_assinatura_invalida(conn):
    payload = b'{"id":"evt_2","type":"x"}'
    with pytest.raises(InvalidSignature):
        handle_webhook(conn, payload, "deadbeef", SECRET)

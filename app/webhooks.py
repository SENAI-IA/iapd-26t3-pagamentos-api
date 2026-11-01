"""Recebimento de webhooks do adquirente.

Regras:
- Verificar a assinatura HMAC antes de qualquer processamento.
- Idempotência: o mesmo event_id nunca é processado duas vezes (o adquirente reenvia).
"""
import json
import sqlite3

from app.auth import verify_signature
from app.ledger import credit
from app.payments import capture_payment, now_utc

MERCHANT_ACCOUNT = "merchant"


class InvalidSignature(Exception):
    pass


def _already_seen(conn: sqlite3.Connection, event_id: str) -> bool:
    row = conn.execute("SELECT 1 FROM webhook_events WHERE event_id = ?", (event_id,)).fetchone()
    return row is not None


def handle_webhook(conn: sqlite3.Connection, payload: bytes, signature: str, secret: str) -> str:
    if not verify_signature(payload, signature, secret):
        raise InvalidSignature()
    event = json.loads(payload)
    event_id = event["id"]
    with conn:
        conn.execute(
            "INSERT OR REPLACE INTO webhook_events(event_id, received_at) VALUES (?, ?)",
            (event_id, now_utc().isoformat()),
        )
    if event["type"] == "payment.captured":
        payment = capture_payment(conn, int(event["payment_id"]))
        credit(conn, MERCHANT_ACCOUNT, payment["amount_cents"], f"capture:{payment['id']}")
        return "processed"
    return "ignored"

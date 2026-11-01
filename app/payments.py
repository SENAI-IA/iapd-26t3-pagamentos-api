"""Ciclo de vida de um pagamento: pending -> captured.

Regras:
- Timestamps sempre em UTC com tzinfo (datetime.now(timezone.utc)).
- Nunca registrar o PAN completo em log; só os 4 últimos dígitos.
- Erros são exceções tipadas; nenhuma função devolve None para sinalizar falha.
"""
import logging
import sqlite3
from datetime import datetime, timezone

log = logging.getLogger(__name__)


class PaymentNotFound(Exception):
    pass


class InvalidPaymentState(Exception):
    pass


def mask_pan(pan: str) -> str:
    return "*" * (len(pan) - 4) + pan[-4:]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_payment(conn: sqlite3.Connection, customer_id: str, amount_cents: int, card_pan: str) -> int:
    if amount_cents <= 0:
        raise ValueError("amount_cents deve ser positivo")
    created_at = now_utc().isoformat()
    log.info(
        "payment created customer=%s amount=%s card=%s",
        customer_id, amount_cents, mask_pan(card_pan),
    )
    with conn:
        cur = conn.execute(
            "INSERT INTO payments(customer_id, amount_cents, status, created_at, card_last4) "
            "VALUES (?, ?, 'pending', ?, ?)",
            (customer_id, amount_cents, created_at, card_pan[-4:]),
        )
    return cur.lastrowid


def get_payment(conn: sqlite3.Connection, payment_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM payments WHERE id = ?", (payment_id,)).fetchone()
    if row is None:
        raise PaymentNotFound(payment_id)
    return row


def capture_payment(conn: sqlite3.Connection, payment_id: int) -> sqlite3.Row:
    """Move o pagamento de pending para captured. Falha alto se não existir."""
    payment = get_payment(conn, payment_id)
    if payment["status"] != "pending":
        raise InvalidPaymentState(f"pagamento {payment_id} está em {payment['status']}")
    with conn:
        conn.execute("UPDATE payments SET status = 'captured' WHERE id = ?", (payment_id,))
    return get_payment(conn, payment_id)

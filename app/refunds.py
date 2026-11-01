"""Reembolsos parciais e totais.

Regra de ouro: a soma dos reembolsos de um pagamento nunca passa do valor capturado.
"""
import sqlite3

from app.payments import get_payment, now_utc


class RefundError(Exception):
    pass


def total_refunded(conn: sqlite3.Connection, payment_id: int) -> int:
    row = conn.execute(
        "SELECT COALESCE(SUM(amount_cents), 0) AS total FROM refunds WHERE payment_id = ?",
        (payment_id,),
    ).fetchone()
    return int(row["total"])


def refund(conn: sqlite3.Connection, payment_id: int, amount_cents: int) -> int:
    payment = get_payment(conn, payment_id)
    if payment["status"] != "captured":
        raise RefundError("só pagamentos capturados podem ser reembolsados")
    if amount_cents <= 0:
        raise RefundError("valor do reembolso deve ser positivo")
    already = total_refunded(conn, payment_id)
    if already + amount_cents > payment["amount_cents"]:
        raise RefundError(
            f"reembolso de {amount_cents} excede o saldo reembolsável "
            f"({payment['amount_cents'] - already})"
        )
    with conn:
        cur = conn.execute(
            "INSERT INTO refunds(payment_id, amount_cents, created_at) VALUES (?, ?, ?)",
            (payment_id, amount_cents, now_utc().isoformat()),
        )
    return cur.lastrowid

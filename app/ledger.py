"""Razão contábil: saldo das contas e lançamentos.

Regras:
- Débito é uma única instrução UPDATE condicional (atômica no SQLite); nunca
  ler o saldo em Python, decidir e escrever de volta.
- Consultas em lote usam IN (...), nunca uma query por item.
"""
import sqlite3

from app.payments import now_utc


class InsufficientFunds(Exception):
    pass


def open_account(conn: sqlite3.Connection, account_id: str, initial_cents: int = 0) -> None:
    with conn:
        conn.execute(
            "INSERT INTO accounts(id, balance_cents) VALUES (?, ?)",
            (account_id, initial_cents),
        )


def balance(conn: sqlite3.Connection, account_id: str) -> int:
    row = conn.execute("SELECT balance_cents FROM accounts WHERE id = ?", (account_id,)).fetchone()
    if row is None:
        raise KeyError(account_id)
    return int(row["balance_cents"])


def credit(conn: sqlite3.Connection, account_id: str, cents: int, reason: str) -> None:
    if cents <= 0:
        raise ValueError("crédito deve ser positivo")
    with conn:
        conn.execute(
            "UPDATE accounts SET balance_cents = balance_cents + ? WHERE id = ?",
            (cents, account_id),
        )
        conn.execute(
            "INSERT INTO ledger_entries(account_id, delta_cents, reason, created_at) VALUES (?, ?, ?, ?)",
            (account_id, cents, reason, now_utc().isoformat()),
        )


def debit(conn: sqlite3.Connection, account_id: str, cents: int, reason: str) -> None:
    """Debita de forma atômica: o próprio UPDATE verifica o saldo."""
    if cents <= 0:
        raise ValueError("débito deve ser positivo")
    with conn:
        cur = conn.execute(
            "UPDATE accounts SET balance_cents = balance_cents - ? "
            "WHERE id = ? AND balance_cents >= ?",
            (cents, account_id, cents),
        )
        if cur.rowcount == 0:
            raise InsufficientFunds(account_id)
        conn.execute(
            "INSERT INTO ledger_entries(account_id, delta_cents, reason, created_at) VALUES (?, ?, ?, ?)",
            (account_id, -cents, reason, now_utc().isoformat()),
        )


def statement(conn: sqlite3.Connection, account_ids: list[str]) -> dict[str, dict]:
    """Saldo e lançamentos de várias contas em duas consultas, não em 2N."""
    if not account_ids:
        return {}
    marks = ",".join("?" * len(account_ids))
    result: dict[str, dict] = {}
    for row in conn.execute(f"SELECT id, balance_cents FROM accounts WHERE id IN ({marks})", account_ids):
        result[row["id"]] = {"balance_cents": row["balance_cents"], "entries": []}
    for row in conn.execute(
        f"SELECT account_id, delta_cents, reason, created_at FROM ledger_entries "
        f"WHERE account_id IN ({marks}) ORDER BY id",
        account_ids,
    ):
        result[row["account_id"]]["entries"].append(dict(row))
    return result

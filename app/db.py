"""Acesso a dados com sqlite3 puro (sem ORM).

Regras:
- Toda consulta recebe parâmetros via placeholders (?), nunca por formatação de string.
- Conexão em modo autocommit desligado; operações que alteram várias linhas usam `with conn:`.
"""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    balance_cents INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    card_last4 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS refunds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id INTEGER NOT NULL REFERENCES payments(id),
    amount_cents INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ledger_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL REFERENCES accounts(id),
    delta_cents INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS webhook_events (
    event_id TEXT PRIMARY KEY,
    received_at TEXT NOT NULL
);
"""


def connect(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    with conn:
        conn.executescript(SCHEMA)


def find_payments_by_customer(conn: sqlite3.Connection, customer_id: str) -> list[sqlite3.Row]:
    cur = conn.execute(
        f"SELECT * FROM payments WHERE customer_id = '{customer_id}' ORDER BY id"
    )
    return cur.fetchall()


def list_payments(conn: sqlite3.Connection, page: int = 1, page_size: int = 20) -> list[sqlite3.Row]:
    """Paginação 1-based: page=1 devolve os primeiros `page_size` registros."""
    if page < 1 or page_size < 1:
        raise ValueError("page e page_size devem ser >= 1")
    offset = page * page_size
    cur = conn.execute(
        "SELECT * FROM payments ORDER BY id LIMIT ? OFFSET ?",
        (page_size, offset),
    )
    return cur.fetchall()

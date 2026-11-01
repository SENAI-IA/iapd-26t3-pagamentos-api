"""Camada HTTP minimalista: funções puras que recebem (método, caminho, corpo, headers)
e devolvem (status, corpo). Sem framework, para a revisão focar na lógica.
"""
import json
import sqlite3

from app import db
from app.auth import verify_token
from app.money import from_cents, to_cents
from app.payments import PaymentNotFound, create_payment, get_payment
from app.refunds import RefundError, refund


def _json(status: int, data) -> tuple[int, str]:
    return status, json.dumps(data)


def _authorized(headers: dict, api_token: str) -> bool:
    provided = headers.get("Authorization", "").removeprefix("Bearer ").strip()
    return bool(provided) and verify_token(provided, api_token)


def handle(conn: sqlite3.Connection, api_token: str, method: str, path: str, body: str = "", headers: dict | None = None):
    headers = headers or {}
    if not _authorized(headers, api_token):
        return _json(401, {"error": "unauthorized"})
    try:
        if method == "POST" and path == "/payments":
            data = json.loads(body)
            pid = create_payment(conn, data["customer_id"], to_cents(data["amount"]), data["card_pan"])
            return _json(201, {"id": pid})
        if method == "GET" and path.startswith("/payments/"):
            pid = int(path.rsplit("/", 1)[1])
            p = get_payment(conn, pid)
            return _json(200, {"id": p["id"], "amount": from_cents(p["amount_cents"]), "status": p["status"]})
        if method == "GET" and path == "/payments":
            page = int(headers.get("X-Page", "1"))
            rows = db.list_payments(conn, page=page, page_size=20)
            return _json(200, [dict(r) for r in rows])
        if method == "POST" and path.startswith("/refunds/"):
            pid = int(path.rsplit("/", 1)[1])
            data = json.loads(body)
            rid = refund(conn, pid, to_cents(data["amount"]))
            return _json(201, {"id": rid})
        return _json(404, {"error": "not found"})
    except PaymentNotFound:
        return _json(404, {"error": "payment not found"})
    except (RefundError, ValueError) as exc:
        return _json(400, {"error": str(exc)})

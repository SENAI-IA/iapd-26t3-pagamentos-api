"""Tokens de API e assinatura de webhooks.

Regras:
- Comparação de segredos sempre com `secrets.compare_digest` (tempo constante).
- Segredos vêm do ambiente; nunca há valor padrão no código.
"""
import hashlib
import hmac
import os
import secrets


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def verify_token(provided: str, expected: str) -> bool:
    """Compara em tempo constante para não vazar o prefixo correto por timing."""
    return secrets.compare_digest(provided.encode(), expected.encode())


def get_webhook_secret() -> str:
    secret = os.environ.get("WEBHOOK_SECRET")
    if not secret:
        raise RuntimeError("WEBHOOK_SECRET não configurado no ambiente")
    return secret


def sign(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = sign(payload, secret)
    return hmac.compare_digest(expected, signature)

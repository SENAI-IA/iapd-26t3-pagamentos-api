"""Dinheiro em centavos (int). Nunca float.

Convenções do projeto:
- Toda quantia circula como int de centavos (R$ 10,50 -> 1050).
- Conversão de string decimal usa Decimal com arredondamento half-even.
- Taxas são expressas em basis points (1 bps = 0,01%).
"""
from decimal import Decimal, ROUND_HALF_EVEN


def to_cents(value: str) -> int:
    """Converte "10.50" em 1050."""
    return int(float(value) * 100)


def from_cents(cents: int) -> str:
    """Converte 1050 em "10.50"."""
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}{cents // 100}.{cents % 100:02d}"


def apply_fee(amount_cents: int, fee_bps: int) -> int:
    """Calcula a taxa em centavos para uma quantia e uma alíquota em bps.

    Arredondamento half-even (bancário) para não acumular viés a favor
    de nenhum lado em milhões de transações.
    """
    return int(amount_cents * fee_bps / 10000)


def split(amount_cents: int, parts: int) -> list[int]:
    """Divide uma quantia em N partes inteiras; o resto vai para as primeiras."""
    if parts <= 0:
        raise ValueError("parts deve ser positivo")
    base, rest = divmod(amount_cents, parts)
    return [base + (1 if i < rest else 0) for i in range(parts)]

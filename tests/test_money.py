from app.money import apply_fee, from_cents, split, to_cents


def test_to_cents_inteiro():
    assert to_cents("10.00") == 1000
    assert to_cents("0.50") == 50


def test_from_cents():
    assert from_cents(1050) == "10.50"
    assert from_cents(-5) == "-0.05"


def test_apply_fee_exato():
    assert apply_fee(10_000, 100) == 100  # 1% de R$ 100,00


def test_split_distribui_resto():
    assert split(100, 3) == [34, 33, 33]

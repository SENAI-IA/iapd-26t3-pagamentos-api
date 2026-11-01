import pytest

from app import db
from app.payments import InvalidPaymentState, capture_payment, create_payment, get_payment, mask_pan
from app.refunds import RefundError, refund, total_refunded


def test_mask_pan():
    assert mask_pan("4111111111111111") == "************1111"


def test_create_e_capture(conn):
    pid = create_payment(conn, "c1", 2500, "4111111111111111")
    assert get_payment(conn, pid)["status"] == "pending"
    p = capture_payment(conn, pid)
    assert p["status"] == "captured"
    assert p["card_last4"] == "1111"


def test_capture_duas_vezes_falha(conn):
    pid = create_payment(conn, "c1", 2500, "4111111111111111")
    capture_payment(conn, pid)
    with pytest.raises(InvalidPaymentState):
        capture_payment(conn, pid)


def test_valor_invalido(conn):
    with pytest.raises(ValueError):
        create_payment(conn, "c1", 0, "4111111111111111")


def test_busca_por_cliente(conn):
    create_payment(conn, "c1", 100, "4111111111111111")
    create_payment(conn, "c2", 200, "4111111111111111")
    rows = db.find_payments_by_customer(conn, "c1")
    assert [r["amount_cents"] for r in rows] == [100]


def test_list_payments_devolve_lista(conn):
    assert isinstance(db.list_payments(conn, page=1, page_size=5), list)


def test_refund_parcial(conn):
    pid = create_payment(conn, "c1", 1000, "4111111111111111")
    capture_payment(conn, pid)
    refund(conn, pid, 300)
    refund(conn, pid, 200)
    assert total_refunded(conn, pid) == 500


def test_refund_de_pending_falha(conn):
    pid = create_payment(conn, "c1", 1000, "4111111111111111")
    with pytest.raises(RefundError):
        refund(conn, pid, 100)

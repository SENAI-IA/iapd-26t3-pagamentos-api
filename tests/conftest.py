import pytest

from app import db
from app.ledger import open_account


@pytest.fixture
def conn():
    c = db.connect(":memory:")
    db.init_schema(c)
    open_account(c, "merchant", 0)
    open_account(c, "alice", 10_000)
    yield c
    c.close()

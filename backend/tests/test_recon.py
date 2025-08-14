from app.schemas_cdm import Trade
from app.recon.engine import reconcile_trades


def test_reconcile_basic():
    internal = [
        Trade(trade_id="T1", product_code="ES", quantity=1, price=10.0),
        Trade(trade_id="T2", product_code="NQ", quantity=2, price=20.0),
    ]
    external = [
        Trade(trade_id="T1", product_code="ES", quantity=1, price=10.0),
        Trade(trade_id="T3", product_code="RTY", quantity=1, price=30.0),
    ]
    res = reconcile_trades(internal, external)
    assert res["summary"]["matches"] == 1
    assert res["summary"]["missing_internal"] == 1
    assert res["summary"]["missing_external"] == 1



from __future__ import annotations

from app.otc.schemas import OTCTrade
from app.otc.recon import reconcile_otc


def test_otc_match_by_uti():
    internal = [OTCTrade(uti="U1", product="IRS", ccy="USD", notional=1_000_000, fixed_rate=0.02)]
    external = [OTCTrade(uti="U1", product="IRS", ccy="USD", notional=1_000_000, fixed_rate=0.02)]
    res = reconcile_otc(internal, external)
    assert res["summary"]["matches"] == 1


def test_otc_field_mismatch_and_tolerance():
    internal = [OTCTrade(uti="U2", product="IRS", ccy="USD", notional=1_000_000, fixed_rate=0.021)]
    external = [OTCTrade(uti="U2", product="IRS", ccy="USD", notional=1_005_000, fixed_rate=0.02)]
    res = reconcile_otc(internal, external, tolerances={"notional": 10_000, "fixed_rate": 0.002})
    ex = [e for e in res["exceptions"] if e["type"] == "FIELD_MISMATCH"]
    assert ex and ex[0]["auto_cleared"] is True



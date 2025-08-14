from app.ml.predict import predict_breaks, train_model, load_training_data
from app.reports.regulatory import validate_regulatory


def test_predict_breaks_shapes():
    df = load_training_data(csv_path=__import__('pathlib').Path('/tmp/none.csv'))
    model = train_model(df)
    preds = predict_breaks(model, [{"trade_id": "T1", "quantity": 2, "price_dev": 0.7}])
    assert len(preds) == 1
    assert 0.0 <= preds[0]["probability"] <= 1.0


def test_regulatory_validation_basic():
    res = validate_regulatory([{"trade_id": "T1", "product_code": "ES", "price": 10, "quantity": 1}])
    assert "EMIR" in res and "passes" in res["EMIR"]



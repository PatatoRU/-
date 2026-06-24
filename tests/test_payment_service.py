from app.services.payment_service import build_ad_payment_payload, parse_ad_payment_payload


def test_ad_payment_payload_roundtrip():
    payload = build_ad_payment_payload(42, "boost", "food-moscow-0")
    assert payload == "adpay:42:boost:food-moscow-0"
    assert parse_ad_payment_payload(payload) == (42, "boost", "food-moscow-0")


def test_ad_payment_payload_rejects_invalid_values():
    assert parse_ad_payment_payload("ad:boost:place") is None
    assert parse_ad_payment_payload("adpay:not-int:boost:place") is None
    assert parse_ad_payment_payload("adpay:1::place") is None

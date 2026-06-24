from __future__ import annotations


def build_ad_payment_payload(payment_id: int, tariff_code: str, external_id: str) -> str:
    return f"adpay:{payment_id}:{tariff_code}:{external_id}"


def parse_ad_payment_payload(payload: str) -> tuple[int, str, str] | None:
    parts = payload.split(":", 3)
    if len(parts) != 4 or parts[0] != "adpay":
        return None
    try:
        payment_id = int(parts[1])
    except ValueError:
        return None
    tariff_code = parts[2].strip()
    external_id = parts[3].strip()
    if not tariff_code or not external_id:
        return None
    return payment_id, tariff_code, external_id

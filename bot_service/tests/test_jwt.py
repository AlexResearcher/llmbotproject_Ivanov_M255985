import pytest

from app.core.jwt import decode_and_validate


def test_decode_and_validate_returns_payload(make_token) -> None:
    token = make_token(sub="42")

    payload = decode_and_validate(token)

    assert payload["sub"] == "42"


def test_decode_and_validate_rejects_garbage_token() -> None:
    with pytest.raises(ValueError):
        decode_and_validate("not-a-jwt")

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = get_password_hash("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_access_and_refresh_types():
    access = create_access_token({"sub": "1"})
    refresh = create_refresh_token({"sub": "1"})

    access_payload = decode_token(access)
    refresh_payload = decode_token(refresh)

    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"
    assert access_payload["sub"] == "1"

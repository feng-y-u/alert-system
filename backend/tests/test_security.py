from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token


def test_password_hash():
    password = "test123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)


def test_access_token():
    data = {"sub": "testuser", "role": "user"}
    token = create_access_token(data)
    assert token is not None

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "testuser"
    assert payload["role"] == "user"
    assert "exp" in payload
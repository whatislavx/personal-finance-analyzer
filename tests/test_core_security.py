from app.core import security

def test_password_hash_and_verify():
    password = "supersecret"
    hashed = security.get_password_hash(password)
    assert security.verify_password(password, hashed)
    assert not security.verify_password("wrong", hashed)
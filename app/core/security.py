import base64
import hashlib
import hmac
import os

try:
    import bcrypt

    _HAS_BCRYPT = True
except Exception:
    bcrypt = None
    _HAS_BCRYPT = False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")
    if _HAS_BCRYPT and bcrypt is not None:
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))

    if not hashed_password.startswith("pbkdf2_sha256$"):
        return False
    _, iterations, salt_b64, hash_b64 = hashed_password.split("$", 3)
    salt = base64.b64decode(salt_b64.encode("ascii"))
    expected = base64.b64decode(hash_b64.encode("ascii"))
    computed = hashlib.pbkdf2_hmac(
        "sha256", password_bytes, salt, int(iterations), dklen=len(expected)
    )
    return hmac.compare_digest(computed, expected)


def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if _HAS_BCRYPT and bcrypt is not None:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    iterations = 390000
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password_bytes, salt, iterations)
    return (
        "pbkdf2_sha256$"
        f"{iterations}$"
        f"{base64.b64encode(salt).decode('ascii')}$"
        f"{base64.b64encode(derived).decode('ascii')}"
    )

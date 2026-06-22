from __future__ import annotations

import hashlib
import hmac
import secrets


PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 120_000


def hash_password(password: str, salt: str | None = None) -> str:
    next_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        next_salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_ALGORITHM}${PASSWORD_ITERATIONS}${next_salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected_digest = stored_hash.split("$", 3)
    except ValueError:
        return False
    if algorithm != PASSWORD_ALGORITHM:
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(digest, expected_digest)


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

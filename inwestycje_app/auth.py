import base64
import hashlib
import os
from datetime import datetime, timezone

from .db import get_connection


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, 120_000
    )
    return base64.b64encode(salt).decode("utf-8") + ":" + base64.b64encode(password_hash).decode("utf-8")


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_b64, hash_b64 = stored_hash.split(":")
        salt = base64.b64decode(salt_b64)
        correct_hash = base64.b64decode(hash_b64)
        test_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, 120_000
        )
        return test_hash == correct_hash
    except Exception:
        return False


def register_user(username: str, password: str):
    username = username.strip().lower()
    if len(username) < 3:
        raise ValueError("Nazwa użytkownika musi mieć co najmniej 3 znaki.")
    if len(password) < 5:
        raise ValueError("Hasło musi mieć co najmniej 5 znaków.")

    connection = get_connection()
    try:
        connection.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (%s, %s, %s)",
            (username, hash_password(password), datetime.now(timezone.utc)),
        )
        connection.commit()
    except Exception as exc:
        connection.rollback()
        if getattr(exc, "sqlstate", None) == "23505":
            raise ValueError("Taki użytkownik już istnieje.") from exc
        raise
    finally:
        connection.close()


def login_user(username: str, password: str):
    username = username.strip().lower()
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (username,),
        ).fetchone()
    finally:
        connection.close()

    if row is None:
        return None
    if verify_password(password, row["password_hash"]):
        return {"id": row["id"], "username": row["username"]}
    return None


def delete_account(user_id: int):
    connection = get_connection()
    try:
        connection.execute("DELETE FROM users WHERE id = %s", (int(user_id),))
        connection.commit()
    finally:
        connection.close()

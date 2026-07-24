from dataclasses import dataclass

import argon2
import psycopg
from argon2.exceptions import VerifyMismatchError

from ui.config import settings

_ph = argon2.PasswordHasher()


@dataclass(frozen=True)
class UserRecord:
    id: str
    email: str
    password_hash: str
    is_admin: bool


def _connect() -> psycopg.Connection:
    return psycopg.connect(settings.sync_database_url())


def get_user_by_email(email: str) -> UserRecord | None:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
                SELECT id::text, email, password_hash, is_admin
                FROM users
                WHERE lower(email) = lower(%s)
                LIMIT 1
                """,
            (email.strip(),),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return UserRecord(
        id=row[0],
        email=row[1],
        password_hash=row[2],
        is_admin=bool(row[3]),
    )


def authenticate_user(email: str, password: str) -> UserRecord | None:
    user = get_user_by_email(email)
    if user is None:
        return None
    try:
        _ph.verify(user.password_hash, password)
    except VerifyMismatchError:
        return None
    return user


def create_user(email: str, password: str, *, is_admin: bool = False) -> str:
    password_hash = _ph.hash(password)
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM users WHERE lower(email) = lower(%s) LIMIT 1",
                (email.strip(),),
            )
            if cur.fetchone() is not None:
                raise ValueError(f"User with email {email} already exists.")
            cur.execute(
                """
                INSERT INTO users (email, password_hash, is_admin)
                VALUES (%s, %s, %s)
                RETURNING id::text
                """,
                (email.strip(), password_hash, is_admin),
            )
            row = cur.fetchone()
        conn.commit()
    assert row is not None
    return row[0]

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

hasher = PasswordHasher()


def hash_value(value: str) -> str:
    return hasher.hash(value)


def validate_value(secret: str, value: str) -> bool:
    try:
        return hasher.verify(secret, value)
    except VerifyMismatchError:
        return False

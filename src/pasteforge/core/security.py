import hashlib
import hmac
import ipaddress
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Request

from pasteforge.core.config import configs
from pasteforge.core.exceptions.exceptions import ForbiddenError

hasher = PasswordHasher()


def hash_value(value: str) -> str:
    return hasher.hash(value)


def validate_value(secret: str, value: str) -> bool:
    try:
        return hasher.verify(secret, value)
    except VerifyMismatchError:
        return False


def generate_csrf_token() -> str:
    return str(uuid.uuid4())


def validate_csrf_token(request: Request) -> None:
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")

    if not csrf_cookie or not csrf_header:
        raise ForbiddenError(message="Both CSRF cookie and header are required.")

    if csrf_cookie != csrf_header:
        raise ForbiddenError(message="CSRF header does not match CSRF cookie.")


def hash_ip(ip: str) -> str:
    normalized_ip = ipaddress.ip_address(ip).compressed

    return hmac.new(
        key=configs.SECRET_KEY.encode(),
        msg=f"pasteforge:anonymous-ip:{normalized_ip}".encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

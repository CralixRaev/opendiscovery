from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


def hash_password(password: str) -> str:
    """
    Hash password using argon2

    :param password:
    :return: argon2 hash
    """
    ph = PasswordHasher()
    return ph.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    ph = PasswordHasher()
    try:
        return ph.verify(hashed_password, password)
    except VerifyMismatchError:
        return False

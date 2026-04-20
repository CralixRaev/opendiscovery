from argon2 import PasswordHasher


def hash_password(password: str) -> str:
    """
    Hash password using argon2

    :param password:
    :return: argon2 hash
    """
    ph = PasswordHasher()
    return ph.hash(password)
import base64
import json
from typing import Any


def decode_unverified_claims(token: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("scanner token must be a JWT")

    payload = parts[1]
    padded_payload = payload + "=" * (-len(payload) % 4)
    decoded = base64.urlsafe_b64decode(padded_payload)
    claims = json.loads(decoded)
    if not isinstance(claims, dict):
        raise ValueError("scanner token payload must be an object")
    return claims

import asyncio
import json
import signal
from typing import Any

import jwt
import nats
from core.config import Config
from jwt import InvalidTokenError
from nats_callout import AdaptixEncoder, AuthError, BaseAuthCalloutService
from nats_callout.claims import AuthRequestData, UserData
from nats_callout.claims.user import PubSubPermissions


AUTH_CALLOUT_SUBJECT = "$SYS.REQ.USER.AUTH"
JWT_ALGORITHM = "HS256"
TENANT_SUBJECT_PREFIX = "opendiscovery.tenants"


# hack :)
class JsonAdaptixEncoder(AdaptixEncoder):
    def json_loads(self, data: str | dict[str, Any]) -> Any:
        if isinstance(data, dict):
            return data
        return json.loads(data)

    def json_dumps(self, data: Any) -> str:
        return json.dumps(data)


class AuthCalloutService(BaseAuthCalloutService):
    def __init__(
        self,
        nkey_seed: str,
        token_secret: str,
        token_issuer: str,
        account: str = "$G",
    ) -> None:
        self.encoder = JsonAdaptixEncoder()
        self.nkey_seed = nkey_seed
        self.token_secret = token_secret
        self.token_issuer = token_issuer
        self.account = account
        self.encoder.kp = self._key_pair

    def _decode_scanner_token(self, token: str | None) -> dict[str, Any]:
        if not token:
            raise AuthError("scanner token is required")

        try:
            payload = jwt.decode(
                token,
                self.token_secret,
                algorithms=[JWT_ALGORITHM],
                issuer=self.token_issuer,
            )
        except InvalidTokenError as exc:
            raise AuthError("invalid scanner token") from exc

        scanner_id = payload.get("scanner_id")
        tenant_id = payload.get("tenant_id")
        subject = payload.get("sub")
        if (
            payload.get("token_use") != "scanner"
            or not isinstance(scanner_id, int)
            or not isinstance(tenant_id, int)
            or subject != str(scanner_id)
        ):
            raise AuthError("invalid scanner token claims")

        return payload

    async def _handle_auth_request_data(
        self,
        auth_request_data: AuthRequestData,
    ) -> UserData:
        connect_opts = auth_request_data.connect_opts
        claims = self._decode_scanner_token(connect_opts.auth_token)

        scanner_id = claims["scanner_id"]
        tenant_id = claims["tenant_id"]

        scanner_subject_prefix = f"{TENANT_SUBJECT_PREFIX}.{tenant_id}.scanners.{scanner_id}"

        return UserData(
            version=auth_request_data.version,
            tags=[
                *auth_request_data.tags,
                "scanner",
                f"scanner:{scanner_id}",
                f"tenant:{tenant_id}",
            ],
            pub=PubSubPermissions(allow=[f"{scanner_subject_prefix}.>"]),
            sub=PubSubPermissions(allow=[f"{scanner_subject_prefix}.>"]),
        )


async def run() -> None:
    settings = Config()
    if not settings.auth_issuer_seed:
        raise RuntimeError(
            "AUTH_ISSUER_SEED is required and must match authorization.auth_callout.issuer"
        )

    service = AuthCalloutService(
        nkey_seed=settings.auth_issuer_seed,
        token_secret=settings.backend_token_secret,
        token_issuer=settings.backend_token_issuer,
        account=settings.nats_account,
    )

    nc = await nats.connect(
        settings.nats_url,
        user=settings.nats_auth_user,
        password=settings.nats_auth_password,
        name="opendiscovery-auth-callout",
    )

    async def handle_auth_request(msg) -> None:
        response = await service(msg.data)
        await msg.respond(response.encode())

    await nc.subscribe(AUTH_CALLOUT_SUBJECT, cb=handle_auth_request)
    await nc.flush()
    print(f"auth callout service is listening on {AUTH_CALLOUT_SUBJECT}")

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    await stop.wait()
    try:
        await nc.drain()
    except Exception:
        await nc.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

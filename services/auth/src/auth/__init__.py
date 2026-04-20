import asyncio
import json
import os
import signal
from typing import Any

import nats
from nats_callout import AdaptixEncoder, AuthError, BaseAuthCalloutService
from nats_callout.claims import AuthRequestData, UserData
from nats_callout.claims.user import PubSubPermissions


AUTH_CALLOUT_SUBJECT = "$SYS.REQ.USER.AUTH"

# hack :)
class JsonAdaptixEncoder(AdaptixEncoder):
    def json_loads(self, data: str | dict[str, Any]) -> Any:
        if isinstance(data, dict):
            return data
        return json.loads(data)

    def json_dumps(self, data: Any) -> str:
        return json.dumps(data)


class AuthCalloutService(BaseAuthCalloutService):
    def __init__(self, nkey_seed: str, account: str = "$G") -> None:
        self.encoder = JsonAdaptixEncoder()
        self.nkey_seed = nkey_seed
        self.account = account
        self.encoder.kp = self._key_pair

    async def _handle_auth_request_data(
        self,
        auth_request_data: AuthRequestData,
    ) -> UserData:
        connect_opts = auth_request_data.connect_opts

        print(connect_opts)

        if connect_opts.user != "demo" or connect_opts.pass_ != "secret":
            name = connect_opts.user or "<missing>"
            raise AuthError(f"invalid credentials for {name}")

        return UserData(
            version=auth_request_data.version,
            tags=auth_request_data.tags,
            pub=PubSubPermissions(allow=[">"]),
            sub=PubSubPermissions(allow=[">"]),
        )


async def run() -> None:
    issuer_seed = os.environ.get("AUTH_ISSUER_SEED")
    if not issuer_seed:
        raise RuntimeError(
            "AUTH_ISSUER_SEED is required and must match authorization.auth_callout.issuer"
        )

    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    service = AuthCalloutService(
        nkey_seed=issuer_seed,
        account=os.environ.get("NATS_ACCOUNT", "$G"),
    )

    nc = await nats.connect(
        nats_url,
        user=os.environ.get("NATS_AUTH_USER", "auth"),
        password=os.environ.get("NATS_AUTH_PASSWORD", "auth"),
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

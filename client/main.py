import asyncio
import os

import nats


async def run() -> None:
    nats_url = os.environ.get("NATS_URL", "nats://localhost:4222")
    nc = await nats.connect(
        nats_url,
        user=os.environ.get("NATS_USER", "demo"),
        password=os.environ.get("NATS_PASSWORD", "secret"),
        name="opendiscovery-demo-client",
    )

    subject = os.environ.get("NATS_DEMO_SUBJECT", "demo.auth_callout")
    sub = await nc.subscribe(subject)
    await nc.flush()

    payload = b"authenticated through auth callout"
    await nc.publish(subject, payload)
    msg = await sub.next_msg(timeout=2)
    print(msg.data.decode())

    await nc.drain()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()

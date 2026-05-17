import asyncio

import nats

from config import ClientConfig


async def run() -> None:
    config = ClientConfig()
    nc = await nats.connect(
        config.nats_url,
        token=config.scanner_token,
        name=config.client_name,
    )

    subject = config.subject
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

# OpenDiscovery scanner client

Requires `nmap` in `PATH`.

## GUI

Run the local scan GUI:

```bash
cd client
uv run python gui.py
```

The GUI accepts an IP address or CIDR network, runs `nmap`, shows alive hosts and open TCP ports, and can export the result as JSON.

## NATS worker

```
export OPENDISCOVERY_SCANNER_TOKEN="<scanner token from /scanners>"
```

optional:
```bash
export OPENDISCOVERY_NATS_URL="nats://localhost:4222"
export OPENDISCOVERY_NATS_SUBJECT="opendiscovery.tenants.<tenant_id>.scanners.<scanner_id>.events"
export OPENDISCOVERY_NATS_CLIENT_NAME="opendiscovery-scanner-client"
```

# generates NATS.io account issuer NKey
generate-keys:
    nsc generate nkey --account
    nsc generate nkey --curve

# creates a new Aerich migration from current Tortoise models
migrate-new name:
    uv run aerich migrate --name "{{name}}"

# applies pending Aerich migrations
migrate:
    uv run aerich upgrade

# shows Aerich migration history
migrate-history:
    uv run aerich history

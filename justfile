# generates NATS.io account issuer NKey
generate-keys:
    nsc generate nkey --account
    nsc generate nkey --curve

# creates a new Tortoise ORM migration from current models
migrate-new name:
    uv run python -m tortoise makemigrations --name "{{name}}"

# applies pending Tortoise ORM migrations
migrate:
    uv run python -m tortoise migrate

# shows applied Tortoise ORM migrations
migrate-history:
    uv run python -m tortoise history

# shows Tortoise ORM migration heads on disk
migrate-heads:
    uv run python -m tortoise heads

# installs git pre-commit hooks
pre-commit-install:
    uv run pre-commit install

# runs pre-commit hooks against all files
pre-commit-run:
    uv run pre-commit run --all-files

# runs Ruff checks against the repository
lint:
    uv run ruff check .

# formats Python files with Ruff
format:
    uv run ruff format .

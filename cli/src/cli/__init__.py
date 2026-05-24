import typer

from cli import database, tenant, test_data, user

app = typer.Typer()
app.add_typer(database.app, name="db")
app.add_typer(tenant.app, name="tenant")
app.add_typer(test_data.app, name="test-data")
app.add_typer(user.app, name="user")

if __name__ == "__main__":
    app()

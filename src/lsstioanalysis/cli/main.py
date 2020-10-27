from __future__ import annotations

__all__ = ["app"]

import typer

app = typer.Typer(help="Inventory and analyze the holdings in lsst.io")


@app.command()
def analyze() -> None:
    """Run analysis."""
    typer.echo("Hello world.")

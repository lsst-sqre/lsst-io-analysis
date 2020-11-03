from __future__ import annotations

__all__ = ["app"]

import asyncio

import httpx
import typer

from lsstioanalysis.ingest import get_ltd_products

app = typer.Typer(help="Inventory and analyze the holdings in lsst.io")


@app.command()
def analyze() -> None:
    """Run analysis."""
    typer.echo("Running analysis.")
    asyncio.run(async_analyze())
    typer.echo("Complete.")


async def async_analyze():
    async with httpx.AsyncClient() as client:
        ltd_products = await get_ltd_products(client)
        print(ltd_products)

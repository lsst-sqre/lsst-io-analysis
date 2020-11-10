from __future__ import annotations

__all__ = ["app"]

import asyncio

import httpx
import typer
from algoliasearch.search_client import SearchClient

from lsstioanalysis.ingest import get_ltd_products

app = typer.Typer(help="Inventory and analyze the holdings in lsst.io")


@app.command()
def analyze(
    algolia_id: str = typer.Option("", envvar="ALGOLIA_ID"),
    algolia_key: str = typer.Option("", envvar="ALGOLIA_KEY"),
    algolia_index_name: str = typer.Option(
        "document_dev", envvar="ALGOLIA_INDEX"
    ),
) -> None:
    """Run analysis."""
    typer.echo("Running analysis.")
    asyncio.run(async_analyze(algolia_id, algolia_key, algolia_index_name))
    typer.echo("Complete.")


async def async_analyze(
    algolia_id: str, algolia_key: str, algolia_index_name: str
) -> None:
    # I couldn't get the async algolia search client to work
    search_client = SearchClient.create(algolia_id, algolia_key)
    async with httpx.AsyncClient() as client:
        algolia_index = search_client.init_index(algolia_index_name)
        ltd_products = await get_ltd_products(client, algolia_index)
        print(ltd_products)

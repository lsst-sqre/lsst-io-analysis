from __future__ import annotations

__all__ = ["app"]

import asyncio
import csv
import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

import httpx
import typer
from algoliasearch.search_client import SearchClient

from lsstioanalysis.ingest import get_ltd_products

if TYPE_CHECKING:
    from lsstioanalysis.ingest import LtdProduct

app = typer.Typer(help="Inventory and analyze the holdings in lsst.io")


@app.command()
def analyze(
    algolia_id: str = typer.Option("", envvar="ALGOLIA_ID"),
    algolia_key: str = typer.Option("", envvar="ALGOLIA_KEY"),
    algolia_index_name: str = typer.Option(
        "document_dev", envvar="ALGOLIA_INDEX"
    ),
    output_csv: Optional[Path] = typer.Option(..., dir_okay=False),
) -> None:
    """Run analysis."""
    typer.echo("Running analysis.")
    asyncio.run(
        async_analyze(algolia_id, algolia_key, algolia_index_name, output_csv)
    )
    typer.echo("Complete.")


async def async_analyze(
    algolia_id: str,
    algolia_key: str,
    algolia_index_name: str,
    output_csv: Optional[Path],
) -> None:
    # I couldn't get the async algolia search client to work
    search_client = SearchClient.create(algolia_id, algolia_key)
    async with httpx.AsyncClient() as client:
        algolia_index = search_client.init_index(algolia_index_name)
        ltd_products = await get_ltd_products(client, algolia_index)
        print(ltd_products)

    if output_csv:
        render_csv(ltd_products, output_csv)


def render_csv(ltd_products: List[LtdProduct], csv_path: Path) -> None:
    with csv_path.open(mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "url",
            "handle",
            "series",
            "title",
            "updated",
            "editions",
            "repo_url",
            "description",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for ltd_product in ltd_products:
            product_dict = dataclasses.asdict(ltd_product)
            writer.writerow(product_dict)

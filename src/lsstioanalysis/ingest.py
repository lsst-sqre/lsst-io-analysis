"""Ingest pipeline for documentation projects."""

from __future__ import annotations

__all__ = ["LtdProduct", "get_ltd_products"]

from typing import List

import httpx
from pydantic import HttpUrl, validator
from pydantic.dataclasses import dataclass

from lsstioanalysis.utils import gather_with_concurrency


@dataclass
class LtdProduct:

    url: HttpUrl

    repo_url: HttpUrl

    title: str

    editions: int

    @validator("url")
    def validate_url(cls, v: HttpUrl) -> HttpUrl:
        if v.path is None:
            v.path = "/"
            return HttpUrl.build(
                scheme=v.scheme,
                user=v.user,
                password=v.password,
                host=v.host,
                tld=v.tld,
                host_type=v.host_type,
                port=v.port,
                path=v.path,
                query=v.query,
                fragment=v.fragment,
            )

        return v

    @validator("repo_url")
    def validate_repo_url(cls, v: HttpUrl) -> HttpUrl:
        if v.path.endswith(".git"):
            v.path = v.path[:-4]
            return HttpUrl.build(
                scheme=v.scheme,
                user=v.user,
                password=v.password,
                host=v.host,
                tld=v.tld,
                host_type=v.host_type,
                port=v.port,
                path=v.path,
                query=v.query,
                fragment=v.fragment,
            )

        return v

    @classmethod
    async def ingest_product(
        cls, client: httpx.AsyncClient, url: str
    ) -> LtdProduct:
        r = await client.get(url)
        product_data = r.json()

        r_editions = await client.get(f"{url}/editions/")
        edition_count = len(r_editions.json()["editions"])

        ltd_product = cls(
            url=product_data["published_url"],
            repo_url=product_data["doc_repo"],
            title=product_data["title"],
            editions=edition_count,
        )

        return ltd_product


async def get_ltd_products(client: httpx.AsyncClient) -> List[LtdProduct]:
    r = await client.get("https://keeper.lsst.codes/products/")
    tasks = [
        LtdProduct.ingest_product(client, product_url)
        for product_url in r.json()["products"]
    ]
    results = await gather_with_concurrency(10, *tasks)
    return results

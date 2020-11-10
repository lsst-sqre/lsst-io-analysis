"""Ingest pipeline for documentation projects."""

from __future__ import annotations

__all__ = ["LtdProduct", "get_ltd_products"]

import datetime
from typing import List, Optional

import httpx
from dateutil import parser as datetime_parser
from dateutil.tz import tzutc
from pydantic import HttpUrl, validator
from pydantic.dataclasses import dataclass

from lsstioanalysis.utils import gather_with_concurrency


@dataclass
class LtdProduct:

    url: HttpUrl

    repo_url: HttpUrl

    title: str

    editions: int

    updated: Optional[datetime.datetime]

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

    @staticmethod
    def parse_utc_datetime(
        datetime_str: Optional[str],
    ) -> Optional[datetime.datetime]:
        """Parse a date string, returning a UTC datetime object."""
        if datetime_str is not None:
            date = (
                datetime_parser.parse(datetime_str)
                .astimezone(tzutc())
                .replace(tzinfo=None)
            )
            return date
        else:
            return None

    @classmethod
    async def ingest_product(
        cls, client: httpx.AsyncClient, url: str
    ) -> LtdProduct:
        r = await client.get(url)
        product_data = r.json()

        r_editions = await client.get(f"{url}/editions/")
        editions = r_editions.json()["editions"]
        edition_count = len(editions)

        datetime_rebuilt = None
        for edition_url in editions:
            r = await client.get(edition_url)
            if r.json()["slug"] == "main":
                date_rebuilt = r.json()["date_rebuilt"]
                datetime_rebuilt = cls.parse_utc_datetime(date_rebuilt)
                break

        ltd_product = cls(
            url=product_data["published_url"],
            repo_url=product_data["doc_repo"],
            title=product_data["title"],
            editions=edition_count,
            updated=datetime_rebuilt,
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

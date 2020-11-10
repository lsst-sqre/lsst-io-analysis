"""Ingest pipeline for documentation projects."""

from __future__ import annotations

__all__ = ["LtdProduct", "get_ltd_products"]

import datetime
from typing import TYPE_CHECKING, List, Optional

import httpx
from dateutil import parser as datetime_parser
from dateutil.tz import tzutc
from pydantic import HttpUrl, validator
from pydantic.dataclasses import dataclass

from lsstioanalysis.utils import gather_with_concurrency

if TYPE_CHECKING:
    from algoliasearch.search_index import SearchIndex


@dataclass
class LtdProduct:

    url: HttpUrl

    repo_url: HttpUrl

    title: str

    description: Optional[str]

    handle: Optional[str]

    series: Optional[str]

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
        cls, client: httpx.AsyncClient, algolia_index: SearchIndex, url: str
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

        base_url = product_data["published_url"]
        if not base_url.endswith("/"):
            base_url = f"{base_url}/"

        try:
            algolia_metadata = await AlgoliaMetadata.search_for_url(
                search_index=algolia_index, base_url=base_url
            )
        except ValueError:
            algolia_metadata = AlgoliaMetadata(
                series=None,
                title=None,
                description=None,
                handle=None,
                content_type=None,
            )

        if algolia_metadata.title:
            title = algolia_metadata.title
        else:
            title = product_data["title"]

        ltd_product = cls(
            url=product_data["published_url"],
            repo_url=product_data["doc_repo"],
            title=title,
            description=algolia_metadata.description,
            handle=algolia_metadata.handle,
            series=algolia_metadata.series,
            editions=edition_count,
            updated=datetime_rebuilt,
        )

        return ltd_product


async def get_ltd_products(
    client: httpx.AsyncClient, algolia_index: SearchIndex
) -> List[LtdProduct]:
    r = await client.get("https://keeper.lsst.codes/products/")
    tasks = [
        LtdProduct.ingest_product(client, algolia_index, product_url)
        for product_url in r.json()["products"]
    ]
    results = await gather_with_concurrency(10, *tasks)
    return results


@dataclass
class AlgoliaMetadata:
    """Additional metadata about an LTD product gathered from Algolia."""

    series: Optional[str]
    """Document series."""

    title: Optional[str]
    """Document title."""

    description: Optional[str]
    """Document description or abstract."""

    handle: Optional[str]
    """Document handle."""

    content_type: Optional[str]
    """Content type."""

    @classmethod
    async def search_for_url(
        cls, *, search_index: SearchIndex, base_url: str
    ) -> AlgoliaMetadata:
        """Create an AlgoliaMetadata from a base documentation url."""
        request_options = {
            "filters": f"baseUrl:{cls.escape_facet_value(base_url)}",
            "attributesToRetrieve": [
                "handle",
                "h1",
                "description",
                "series",
                "contentType",
            ],
        }
        results = search_index.search("", request_options)
        if len(results["hits"]) == 0:
            raise ValueError(f"Algolia record unavailable for {base_url}")

        hit = results["hits"][0]
        return cls(
            title=hit["h1"],
            description=hit["description"],
            series=hit["series"],
            handle=hit["handle"],
            content_type=hit["contentType"],
        )

    @staticmethod
    def escape_facet_value(value: str) -> str:
        """Escape and quote a facet value for an Algolia search."""
        value = value.replace('"', r"\"").replace("'", r"\'")
        value = f'"{value}"'
        return value

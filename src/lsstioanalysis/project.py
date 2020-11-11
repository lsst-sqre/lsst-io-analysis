"""Representation for a documentation project on lsst.io"""

from __future__ import annotations

__all__ = ["Series", "Kind", "Project"]

import datetime
from enum import Enum
from typing import Optional

from pydantic import HttpUrl
from pydantic.dataclasses import dataclass


class Series(str, Enum):
    """Enumeration of series handles."""

    DMTN = "DMTN"
    DMTR = "DMTR"
    ITTN = "ITTN"
    LDM = "LDM"
    LPM = "LPM"
    LSE = "LSE"
    PSTN = "PSTN"
    RTN = "RTN"
    SCTR = "SCTR"
    SITCOMTN = "SITCOMTN"
    SMTN = "SMTN"
    SQR = "SQR"
    TSTN = "TSTN"


class Kind(str, Enum):

    document = "document"

    guide = "guide"


@dataclass
class Project:
    """A documentation project."""

    title: str
    """Title of the documentation project."""

    url: HttpUrl
    """The root URL of the documentation's homepage."""

    repo_url: Optional[HttpUrl]
    """Source repository that backs the documentation project (typically a
    GitHub repository).
    """

    series: Optional[Series]
    """The document series."""

    updated: datetime.datetime
    """Date when the main edition was last updated."""

    editions: int
    """The number of editions that this documentation project has."""

    in_docushare: bool = False
    """Is this project also backed by DocuShare?"""

    kind: Kind = Kind.guide
    """The documentat's type: either a document or a guide."""

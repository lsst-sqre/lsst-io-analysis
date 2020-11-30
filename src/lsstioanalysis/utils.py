from __future__ import annotations

__all__ = ["gather_with_concurrency"]

import asyncio
from typing import Any, List


async def gather_with_concurrency(n: int, *tasks: Any) -> List[Any]:
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task: Any) -> Any:
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))

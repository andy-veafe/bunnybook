import asyncio
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Callable, TypeVar

_executor = ThreadPoolExecutor()

T = TypeVar("T")


async def run_in_executor(func: Callable[..., T], *args) -> T:
    """
    Execute async function in a separate thread, without blocking the main event
    loop.

    :param func: async function that will be executed in separate thread
    :param args: async function parameters
    :return: async function result
    """
    return await asyncio.get_event_loop().run_in_executor(_executor, func, *args)

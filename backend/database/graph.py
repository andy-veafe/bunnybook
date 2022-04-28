from typing import Callable

from neo4j import GraphDatabase as Neo4JGraphDb, Neo4jDriver

from common.concurrency import run_in_executor


class AsyncGraphDatabase:
    """Async wrapper over Neo4j driver, since it doesn't natively expose an
    async interface.

    HTTP APIs + httpx could have been used to avoid the need for run_in_executor
    calls, at the cost of less convenient responses parsing and slightly worse
    performance."""

    def __init__(self, uri: str, user: str, password: str):
        self._driver: Neo4jDriver = Neo4JGraphDb.driver(uri, auth=(user, password))

    async def write_tx(self, tx_func: Callable):
        """Async wrapper over Neo4j 'write_transaction' method."""

        def write_transaction():
            with self._driver.session() as session:
                return session.write_transaction(tx_func)

        return await run_in_executor(write_transaction)

    async def read_tx(self, tx_func: Callable):
        """Async wrapper over Neo4j 'read_transaction' method."""

        def read_transaction():
            with self._driver.session() as session:
                return session.read_transaction(tx_func)

        return await run_in_executor(read_transaction)

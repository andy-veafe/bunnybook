from loguru import logger

__all__ = "logger"

logger.add(
    "./temp/logs/root.log",
    rotation="1 hour",
    retention="10 days",
    encoding="utf-8",
)

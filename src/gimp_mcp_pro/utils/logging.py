"""Logging configuration for GIMP MCP Pro."""

from __future__ import annotations

import logging
import sys


def setup_logging(
    level: int = logging.INFO,
    debug: bool = False,
) -> logging.Logger:
    """Configure logging for GIMP MCP Pro.

    Logs go to stderr so they don't interfere with MCP stdio transport.
    """
    if debug:
        level = logging.DEBUG

    logger = logging.getLogger("gimp_mcp_pro")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

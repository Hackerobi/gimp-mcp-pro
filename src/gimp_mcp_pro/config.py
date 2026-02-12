"""Configuration for GIMP MCP Pro server."""

from __future__ import annotations

import os

from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Server configuration, loaded from environment variables."""

    gimp_host: str = Field(
        default_factory=lambda: os.getenv("GIMP_MCP_HOST", "localhost"),
        description="GIMP plugin socket host",
    )
    gimp_port: int = Field(
        default_factory=lambda: int(os.getenv("GIMP_MCP_PORT", "9877")),
        description="GIMP plugin socket port",
    )
    timeout: float = Field(
        default_factory=lambda: float(os.getenv("GIMP_MCP_TIMEOUT", "30")),
        description="Default command timeout in seconds",
    )
    log_level: str = Field(
        default_factory=lambda: os.getenv("GIMP_MCP_LOG_LEVEL", "INFO"),
        description="Logging level",
    )
    debug: bool = Field(
        default_factory=lambda: os.getenv("GIMP_MCP_DEBUG", "").lower() in ("1", "true", "yes"),
        description="Enable debug mode",
    )
    use_length_prefix: bool = Field(
        default_factory=lambda: os.getenv("GIMP_MCP_LENGTH_PREFIX", "true").lower()
        in ("1", "true", "yes"),
        description="Use length-prefixed framing (set false for maorcc plugin compat)",
    )

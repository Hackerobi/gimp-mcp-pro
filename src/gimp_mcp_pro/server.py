"""GIMP MCP Pro — Main MCP server entry point.

This module creates the FastMCP server, initializes the GimpBridge,
and registers all tools, resources, and prompts.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from gimp_mcp_pro.bridge import GimpBridge
from gimp_mcp_pro.config import ServerConfig
from gimp_mcp_pro.utils.logging import setup_logging

logger = logging.getLogger("gimp_mcp_pro.server")


def create_server(config: ServerConfig | None = None) -> FastMCP:
    if config is None:
        config = ServerConfig()

    setup_logging(debug=config.debug)
    logger.info(f"Initializing GIMP MCP Pro server (GIMP at {config.gimp_host}:{config.gimp_port})")

    mcp = FastMCP("GIMP MCP Pro")

    bridge = GimpBridge(
        host=config.gimp_host,
        port=config.gimp_port,
        timeout=config.timeout,
        use_length_prefix=config.use_length_prefix,
    )

    from gimp_mcp_pro.tools.image_tools import register_image_tools
    from gimp_mcp_pro.tools.layer_tools import register_layer_tools
    from gimp_mcp_pro.tools.selection_tools import register_selection_tools
    from gimp_mcp_pro.tools.drawing_tools import register_drawing_tools
    from gimp_mcp_pro.tools.inspect_tools import register_inspect_tools
    from gimp_mcp_pro.tools.history_tools import register_history_tools
    from gimp_mcp_pro.tools.pdb_tools import register_pdb_tools
    from gimp_mcp_pro.tools.transform_tools import register_transform_tools
    from gimp_mcp_pro.tools.filter_tools import register_filter_tools
    from gimp_mcp_pro.tools.color_tools import register_color_tools

    register_image_tools(mcp, bridge)
    register_layer_tools(mcp, bridge)
    register_selection_tools(mcp, bridge)
    register_drawing_tools(mcp, bridge)
    register_inspect_tools(mcp, bridge)
    register_history_tools(mcp, bridge)
    register_pdb_tools(mcp, bridge)
    register_transform_tools(mcp, bridge)
    register_filter_tools(mcp, bridge)
    register_color_tools(mcp, bridge)

    logger.info("All tool modules registered")

    prompts_dir = Path(__file__).parent / "prompts"

    @mcp.prompt(description="GIMP MCP best practices")
    def gimp_best_practices() -> str:
        path = prompts_dir / "best_practices.md"
        return path.read_text() if path.exists() else "# Best Practices\n"

    @mcp.prompt(description="Iterative workflow guidance")
    def gimp_iterative_workflow() -> str:
        path = prompts_dir / "iterative_workflow.md"
        return path.read_text() if path.exists() else "# Iterative Workflow\n"

    @mcp.prompt(description="Filter and effects catalog")
    def gimp_filter_catalog() -> str:
        path = prompts_dir / "filter_catalog.md"
        return path.read_text() if path.exists() else "# Filter Catalog\n"

    @mcp.prompt(description="GIMP 3.0 API quick reference")
    def gimp_api_reference() -> str:
        path = prompts_dir / "api_reference.md"
        return path.read_text() if path.exists() else "# API Reference\n"

    logger.info("Prompts registered")
    return mcp


def main() -> None:
    config = ServerConfig()
    mcp = create_server(config)
    logger.info("Starting GIMP MCP Pro server...")
    mcp.run()


if __name__ == "__main__":
    main()

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
    """Create and configure the GIMP MCP Pro server.

    This is the main factory function that:
    1. Creates the FastMCP server
    2. Initializes the GimpBridge for GIMP communication
    3. Registers all tool modules
    4. Registers MCP prompts for AI guidance
    """
    if config is None:
        config = ServerConfig()

    setup_logging(debug=config.debug)
    logger.info(f"Initializing GIMP MCP Pro server (GIMP at {config.gimp_host}:{config.gimp_port})")

    # Create FastMCP server
    mcp = FastMCP("GIMP MCP Pro")

    # Create the bridge (lazy connect — connects on first command)
    bridge = GimpBridge(
        host=config.gimp_host,
        port=config.gimp_port,
        timeout=config.timeout,
        use_length_prefix=config.use_length_prefix,
    )

    # ------------------------------------------------------------------
    # Register tool modules
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Register MCP prompts (AI guidance documents)
    # ------------------------------------------------------------------

    prompts_dir = Path(__file__).parent / "prompts"

    @mcp.prompt(
        description="GIMP MCP best practices — filling shapes, bezier paths, variable persistence, common mistakes to avoid"
    )
    def gimp_best_practices() -> str:
        """Best practices for GIMP operations via MCP. Read this before complex drawing tasks."""
        path = prompts_dir / "best_practices.md"
        if path.exists():
            return path.read_text()
        return (
            "# GIMP MCP Best Practices\n\n"
            "## Key Rules\n"
            "1. Use polygon selection + fill for solid shapes (NOT paintbrush)\n"
            "2. Always call select_none after filling a selection\n"
            "3. Use separate layers for separate elements\n"
            "4. Avoid feathering unless explicitly needed for artistic effect\n"
            "5. Check your work with get_image_bitmap after every 3-5 operations\n"
            "6. Variables and imports persist between execute_python calls\n"
            "7. Always use begin_undo_group/end_undo_group for multi-step workflows\n"
        )

    @mcp.prompt(
        description="Iterative workflow guidance for building complex images with proper layer management and continuous validation"
    )
    def gimp_iterative_workflow() -> str:
        """How to build complex images step by step with validation at each phase."""
        path = prompts_dir / "iterative_workflow.md"
        if path.exists():
            return path.read_text()
        return (
            "# Iterative Workflow\n\n"
            "## Golden Rule: Check after every 3-5 operations\n\n"
            "## Phases\n"
            "1. **Plan**: Check get_image_metadata, plan layer structure\n"
            "2. **Setup layers**: Create all layers BEFORE drawing\n"
            "3. **Draw incrementally**: Draw on correct layer, validate with get_image_bitmap\n"
            "4. **Fix issues**: On the correct layer, don't paint over problems\n"
            "5. **Repeat**: Continue only when current phase looks correct\n"
        )

    @mcp.prompt(
        description="Complete catalog of available filters, effects, and color adjustments with parameters and usage tips"
    )
    def gimp_filter_catalog() -> str:
        """What filters/effects are available and how to use them."""
        path = prompts_dir / "filter_catalog.md"
        if path.exists():
            return path.read_text()
        return "# Filter Catalog\nSee filter_tools and color_tools for available operations.\n"

    @mcp.prompt(
        description="GIMP 3.0 PyGObject API quick reference — working methods, deprecated methods, required imports"
    )
    def gimp_api_reference() -> str:
        """Quick reference for GIMP 3.0 API when using execute_python."""
        path = prompts_dir / "api_reference.md"
        if path.exists():
            return path.read_text()
        return "# API Reference\nSee GIMP developer docs at developer.gimp.org/api/3.0/libgimp/\n"

    logger.info("Prompts registered")

    return mcp


def main() -> None:
    """CLI entry point for gimp-mcp-pro."""
    config = ServerConfig()
    mcp = create_server(config)

    logger.info("Starting GIMP MCP Pro server...")
    mcp.run()


if __name__ == "__main__":
    main()

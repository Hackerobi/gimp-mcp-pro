"""PDB discovery and raw execution tools for GIMP MCP Pro.

The PDB (Procedure Database) is GIMP's registry of all available operations.
These tools let AI assistants discover what's available and use advanced
operations that don't have dedicated typed tools yet.
"""

from __future__ import annotations

import logging
from typing import Any

from gimp_mcp_pro.bridge import GimpBridge, LONG_TIMEOUT
from gimp_mcp_pro.models.common import OperationResult
from gimp_mcp_pro.utils.errors import GimpCommandError

logger = logging.getLogger("gimp_mcp_pro.tools.pdb")


def register_pdb_tools(mcp: Any, bridge: GimpBridge) -> None:
    """Register PDB discovery and raw execution tools."""

    @mcp.tool()
    def search_pdb(query: str, max_results: int = 20) -> dict[str, Any]:
        """Search GIMP's Procedure Database for available operations.

        GIMP has thousands of procedures (filters, file operations, etc.).
        Use this to discover what's available.

        Args:
            query: Search term (e.g., "blur", "sharpen", "file-png", "color")
            max_results: Maximum results to return (default 20)

        Returns:
            List of matching procedure names.
        """
        code = [
            "import json",
            "pdb = Gimp.get_pdb()",
            "if not pdb: raise RuntimeError('PDB not available')",
            f"query = '{query}'.lower()",
            f"max_r = {max_results}",
            "results = []",
            "prefixes = ['gimp-', 'file-', 'plug-in-', 'script-fu-', 'python-fu-']",
            "test_names = [f'{p}{query}' for p in prefixes] + [f'{p}{query}-*' for p in prefixes] + [query]",
            "for name in test_names:\n"
            "    proc = pdb.lookup_procedure(name)\n"
            "    if proc:\n"
            "        results.append(name)\n"
            "        if len(results) >= max_r: break",
            "print(json.dumps(results))",
        ]
        try:
            result = bridge.execute_python(code)
            import json as _json
            procedures = []
            for out in result.get("results", []):
                if out and out.strip():
                    try:
                        procedures = _json.loads(out.strip())
                        break
                    except _json.JSONDecodeError:
                        continue

            return OperationResult.ok(
                operation="search_pdb",
                message=f"Found {len(procedures)} procedure(s) matching '{query}'",
                data={"query": query, "procedures": procedures},
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(operation="search_pdb", error=str(e)).model_dump()

    @mcp.tool()
    def execute_python(
        code: list[str],
        timeout_seconds: float = 30.0,
    ) -> dict[str, Any]:
        """Execute raw Python code in GIMP's PyGObject console.

        This is the ESCAPE HATCH for operations that don't have a dedicated
        typed tool. Use typed tools whenever possible — they have better
        error handling and validation.

        The code runs in GIMP's persistent Python context:
        - Imports persist between calls
        - Variables persist between calls
        - Gimp and Gegl modules are pre-imported

        IMPORTANT: Always call Gimp.displays_flush() after drawing operations.
        Always call Gimp.Selection.none(image) after selection-based operations.

        Args:
            code: List of Python code strings to execute sequentially.
                  Example: ["x = 5", "print(x + 1)"]
            timeout_seconds: Timeout for execution (default 30, use longer for
                            heavy operations like filters)

        Returns:
            Result with stdout output from each line.
        """
        if not code:
            return OperationResult.fail(
                operation="execute_python", error="No code provided"
            ).model_dump()

        timeout = min(timeout_seconds, LONG_TIMEOUT)

        try:
            result = bridge.execute_python(code, timeout=timeout)
            return OperationResult.ok(
                operation="execute_python",
                message="Code executed successfully",
                data={
                    "outputs": result.get("results", []),
                    "lines_executed": len(code),
                },
            ).model_dump()
        except GimpCommandError as e:
            return OperationResult.fail(
                operation="execute_python",
                error=str(e),
                data={"gimp_traceback": e.gimp_traceback} if hasattr(e, "gimp_traceback") else None,
            ).model_dump()

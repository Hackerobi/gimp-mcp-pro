#!/usr/bin/env bash
# GIMP MCP Pro — Setup Script
# Installs the MCP server and copies the GIMP plugin.

set -e

echo "=== GIMP MCP Pro Setup ==="
echo ""

# Check Python version
PYTHON=${PYTHON:-python3}
PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python: $PY_VERSION"

if $PYTHON -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
    echo "  ✓ Python >= 3.10"
else
    echo "  ✗ Python 3.10+ required (found $PY_VERSION)"
    exit 1
fi

# Install the MCP server
echo ""
echo "Installing GIMP MCP Pro..."
pip install -e . --quiet 2>&1 | tail -3
echo "  ✓ MCP server installed"

# Determine GIMP plugin directory
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLUG_DIR="$HOME/Library/Application Support/GIMP/3.0/plug-ins/gimp-mcp-pro"
else
    PLUG_DIR="$HOME/.config/GIMP/3.0/plug-ins/gimp-mcp-pro"
fi

# Install GIMP plugin
echo ""
echo "Installing GIMP plugin to: $PLUG_DIR"
mkdir -p "$PLUG_DIR"
cp gimp_plugin/gimp_mcp_plugin.py "$PLUG_DIR/gimp-mcp-pro"
chmod +x "$PLUG_DIR/gimp-mcp-pro"
echo "  ✓ GIMP plugin installed"

# Verify
echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Open (or restart) GIMP"
echo "  2. In GIMP: Tools → Start MCP Pro Server"
echo "  3. Configure Claude Desktop (see README.md)"
echo ""
echo "Claude Desktop config (add to claude_desktop_config.json):"
echo "  {\"mcpServers\": {\"gimp\": {\"command\": \"gimp-mcp-pro\"}}}"

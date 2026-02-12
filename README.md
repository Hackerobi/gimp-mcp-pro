# GIMP MCP Pro

**Production-grade Model Context Protocol server for GIMP 3.0+**

> 67 typed tools • reliable communication • AI-friendly workflows

GIMP MCP Pro lets AI assistants (Claude, etc.) control GIMP through well-structured, typed MCP tools — creating images, managing layers, drawing shapes, applying filters, adjusting colors, and more.

## Features

- **67 typed MCP tools** across 11 modules — image management, layers, selections, drawing, text, transforms, colors, filters, inspection, history, PDB access
- **Reliable communication** — length-prefixed socket framing (no more JSON boundary guessing)
- **Persistent connections** — one TCP connection, kept alive, with automatic reconnection
- **GIMP 3.0.8 compatible** — tested against current GIMP release using stable APIs (DrawableFilter, PDB procedures)
- **Undo groups** — multi-step AI workflows as a single undo step
- **Pydantic validation** — inputs validated before reaching GIMP
- **AI guidance prompts** — best practices and iterative workflow documentation
- **Visual verification** — `get_image_bitmap` lets AI see what it's drawing
- **PDB discovery** — search GIMP's thousands of procedures
- **Escape hatch** — `execute_python` for anything without a dedicated tool

## Architecture

```
AI Assistant  ←→  MCP Server (gimp-mcp-pro)  ←→  GIMP Plugin
   (Claude)         stdio/SSE                      TCP socket
                    Typed tools                    PyGObject
                    Pydantic models                Native handlers
```

Two processes: the MCP server runs outside GIMP and communicates with a plugin running inside GIMP's Python process via TCP with length-prefixed framing.

## Quick Start

### 1. Install the MCP server

```bash
pip install gimp-mcp-pro
```

Or install from source:

```bash
git clone https://github.com/yourname/gimp-mcp-pro.git
cd gimp-mcp-pro
pip install -e .
```

### 2. Install the GIMP plugin

The setup script handles this automatically:

```bash
./setup.sh
```

Or manually copy the plugin:

```bash
# Linux
PLUG_DIR="$HOME/.config/GIMP/3.0/plug-ins/gimp-mcp-pro"
mkdir -p "$PLUG_DIR"
cp gimp_plugin/gimp_mcp_plugin.py "$PLUG_DIR/gimp-mcp-pro"
chmod +x "$PLUG_DIR/gimp-mcp-pro"

# macOS
PLUG_DIR="$HOME/Library/Application Support/GIMP/3.0/plug-ins/gimp-mcp-pro"
mkdir -p "$PLUG_DIR"
cp gimp_plugin/gimp_mcp_plugin.py "$PLUG_DIR/gimp-mcp-pro"
chmod +x "$PLUG_DIR/gimp-mcp-pro"
```

### 3. Start the plugin in GIMP

Open GIMP → **Tools** → **Start MCP Pro Server**

You should see "MCP Pro: Listening on localhost:9877" in the GIMP console.

### 4. Configure Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gimp": {
      "command": "gimp-mcp-pro"
    }
  }
}
```

Restart Claude Desktop.

### 5. Start editing!

Ask Claude: *"Create an 800x600 image with a red circle in the center and the text 'Hello World' below it"*

## Tool Reference

### Image Management (6 tools)
| Tool | Description |
|------|-------------|
| `create_image` | Create a new blank image |
| `list_images` | List all open images |
| `get_image_info` | Get active image metadata |
| `export_image` | Export as PNG, JPEG, TIFF, BMP, WebP |
| `flatten_image` | Flatten all layers into one |
| `duplicate_image` | Duplicate entire image |

### Layer Operations (9 tools)
| Tool | Description |
|------|-------------|
| `create_layer` | Create a new layer |
| `list_layers` | List all layers with properties |
| `set_active_layer` | Switch working layer |
| `delete_layer` | Delete a layer |
| `set_layer_opacity` | Change layer opacity (0-100) |
| `set_layer_visibility` | Show or hide a layer |
| `duplicate_layer` | Duplicate a layer |
| `merge_visible_layers` | Merge all visible layers |
| `add_alpha_channel` | Add transparency support to a layer |

### Drawing (9 tools)
| Tool | Description |
|------|-------------|
| `set_foreground_color` | Set drawing color |
| `set_background_color` | Set background color |
| `fill_selection` | Fill current selection with color |
| `draw_line` | Draw a straight line |
| `draw_brush_stroke` | Pencil or brush stroke along points |
| `draw_rectangle` | Rectangle (filled or outline) |
| `draw_ellipse` | Ellipse/circle (filled or outline) |
| `draw_polygon` | Polygon (filled or outline) |
| `add_text` | Add a text layer with font/size/color |

### Selections (8 tools)
| Tool | Description |
|------|-------------|
| `select_rectangle` | Rectangular selection |
| `select_ellipse` | Elliptical/circular selection |
| `select_polygon` | Freeform polygon selection |
| `select_all` | Select entire image |
| `select_none` | Clear all selections |
| `select_invert` | Invert current selection |
| `select_grow` | Expand selection by pixels |
| `select_shrink` | Shrink selection by pixels |

### Transforms (11 tools)
| Tool | Description |
|------|-------------|
| `scale_image` | Scale entire image |
| `scale_layer` | Scale a single layer |
| `rotate_image` | Rotate image 90°/180°/270° |
| `rotate_layer` | Rotate layer by arbitrary angle |
| `flip_image` | Flip image horizontal/vertical |
| `flip_layer` | Flip layer horizontal/vertical |
| `crop_image` | Crop to specific rectangle |
| `crop_to_selection` | Crop to selection bounds |
| `autocrop_image` | Auto-trim unused canvas |
| `resize_canvas` | Resize canvas without scaling content |
| `offset_layer` | Move layer position on canvas |

### Color Adjustments (13 tools)
| Tool | Description |
|------|-------------|
| `adjust_brightness_contrast` | Brightness and contrast |
| `adjust_hue_saturation` | Hue, saturation, and lightness |
| `adjust_levels` | Input/output levels with gamma |
| `adjust_curves` | Custom tone curves |
| `desaturate` | Convert to grayscale (multiple methods) |
| `invert_colors` | Negative/invert effect |
| `apply_threshold` | Convert to pure black and white |
| `posterize` | Reduce color levels |
| `color_to_alpha` | Make a color transparent |
| `auto_white_balance` | Automatic levels stretch |
| `get_colors` | Get current foreground/background colors |
| `swap_colors` | Swap foreground and background |
| `sample_color` | Pick color from pixel |

### Filters & Effects (8 tools)
| Tool | Description |
|------|-------------|
| `apply_gaussian_blur` | Gaussian blur |
| `apply_unsharp_mask` | Sharpen with unsharp mask |
| `apply_pixelize` | Pixelization/mosaic effect |
| `apply_edge_detect` | Edge detection (Sobel, Prewitt, Laplace) |
| `apply_emboss` | Emboss/relief effect |
| `apply_noise` | Add random noise/grain |
| `apply_median` | Median denoise filter |
| `apply_drop_shadow` | Drop shadow effect |

### Inspection (4 tools)
| Tool | Description |
|------|-------------|
| `get_image_bitmap` | Get image as viewable PNG (for AI verification) |
| `get_image_metadata` | Fast metadata without pixel data |
| `get_context_state` | Current colors, brush, opacity settings |
| `get_gimp_info` | GIMP version, environment, capabilities |

### History (3 tools)
| Tool | Description |
|------|-------------|
| `begin_undo_group` | Group operations as a single undo step |
| `end_undo_group` | End current undo group |
| `edit_clear` | Clear selection to transparent |

### Advanced (2 tools)
| Tool | Description |
|------|-------------|
| `search_pdb` | Search GIMP's procedure database |
| `execute_python` | Run raw Python in GIMP's console |

## Known Limitations

- **Undo/Redo**: GIMP 3.0's plugin API does not expose programmatic undo/redo. Use `Ctrl+Z`/`Ctrl+Y` in GIMP directly. Undo *groups* work for grouping AI operations.
- **Drop Shadow**: Uses Script-Fu internally; may cause connection issues on some setups.
- **Font Names**: GIMP 3.0 uses names like `Sans-serif`, `Serif`, `Monospace`. The `add_text` tool maps common aliases automatically.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GIMP_MCP_HOST` | `localhost` | GIMP plugin socket host |
| `GIMP_MCP_PORT` | `9877` | GIMP plugin socket port |
| `GIMP_MCP_TIMEOUT` | `30` | Default command timeout (seconds) |
| `GIMP_MCP_LOG_LEVEL` | `INFO` | Logging level |
| `GIMP_MCP_DEBUG` | `false` | Enable debug mode |

## Technical Notes

### Filter Implementation
All filters use `Gimp.DrawableFilter` which safely wraps GEGL operations within GIMP's plugin context. Direct GEGL graph construction (`Gegl.Node()`) crashes in GIMP 3.0 plugin context — this is a known limitation that GIMP MCP Pro works around.

### Color Handling
Colors are accepted as names (`"red"`), hex (`"#FF0000"`), or CSS rgb (`"rgb(255,0,0)"`) across all tools. Internally, colors use Gegl.Color objects with the GIMP 3.0 API.

### Connection Protocol
The MCP server communicates with the GIMP plugin over TCP using 4-byte big-endian length-prefixed JSON messages. This eliminates the fragile JSON boundary detection used by earlier implementations.

## Development

```bash
git clone https://github.com/yourname/gimp-mcp-pro.git
cd gimp-mcp-pro
pip install -e ".[dev]"
pytest
```

## Credits

Built on insights from:
- [maorcc/gimp-mcp](https://github.com/maorcc/gimp-mcp) — proven GIMP plugin architecture, AI guidance prompts
- [slliws/gimp-mcp-server](https://github.com/slliws/gimp-mcp-server) — typed tool module structure
- [libreearth/gimp-mcp](https://github.com/libreearth/gimp-mcp) — original proof-of-concept

## License

MIT

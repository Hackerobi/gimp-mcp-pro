# 🎨 GIMP MCP Pro

**Turn Claude Desktop into a graphics editor.**

A production-grade Model Context Protocol (MCP) server that connects Claude Desktop to GIMP 3.0+. Create images, manage layers, draw shapes, apply filters, adjust colors, and export — all through natural language. 67 typed tools with reliable socket communication.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![GIMP](https://img.shields.io/badge/GIMP-3.0+-green) ![Tools](https://img.shields.io/badge/MCP_Tools-67-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## What This Does

Instead of clicking through GIMP menus and memorizing keyboard shortcuts, you talk to Claude and it does it for you. Ask Claude to:

- *"Create an 800x600 image with a blue gradient background"* → Creates the canvas and draws it
- *"Add a red circle in the center with a drop shadow"* → Draws the shape, applies the filter
- *"Put 'Hello World' in white text at the bottom"* → Adds a text layer with your font/size/color
- *"Make the background layer 50% transparent"* → Adjusts layer opacity instantly
- *"Apply a gaussian blur to the top layer and sharpen the text"* → Runs filters on specific layers
- *"Export as PNG to my desktop"* → Exports in any format (PNG, JPEG, TIFF, BMP, WebP)

All changes happen live in GIMP. You see it update in real time. No scripting. No Script-Fu console.

---

## 🛠️ Integrated Tools (67)

### Image Management (6 tools)
| Tool | Description |
|------|-------------|
| **create_image** | Create a new blank image with custom size and color mode |
| **list_images** | List all open images in GIMP |
| **get_image_info** | Get active image metadata (dimensions, layers, file info) |
| **export_image** | Export as PNG, JPEG, TIFF, BMP, or WebP |
| **flatten_image** | Flatten all layers into one |
| **duplicate_image** | Duplicate the entire image |

### Layer Operations (9 tools)
| Tool | Description |
|------|-------------|
| **create_layer** | Create a new layer with custom name, opacity, blend mode |
| **list_layers** | List all layers with properties |
| **set_active_layer** | Switch the working layer by name or index |
| **delete_layer** | Delete a layer |
| **set_layer_opacity** | Change layer opacity (0-100) |
| **set_layer_visibility** | Show or hide a layer |
| **duplicate_layer** | Duplicate a layer |
| **merge_visible_layers** | Merge all visible layers into one |
| **add_alpha_channel** | Add transparency support to a layer |

### Drawing (9 tools)
| Tool | Description |
|------|-------------|
| **set_foreground_color** | Set drawing color (names, hex, or RGB) |
| **set_background_color** | Set background color |
| **fill_selection** | Fill current selection with foreground/background/white/transparent |
| **draw_line** | Draw a straight line between two points |
| **draw_brush_stroke** | Pencil or paintbrush stroke along a series of points |
| **draw_rectangle** | Rectangle — filled or outline |
| **draw_ellipse** | Ellipse/circle — filled or outline |
| **draw_polygon** | Polygon — filled or outline |
| **add_text** | Add a text layer with font, size, color, and position |

### Selections (8 tools)
| Tool | Description |
|------|-------------|
| **select_rectangle** | Rectangular selection |
| **select_ellipse** | Elliptical/circular selection |
| **select_polygon** | Freeform polygon selection |
| **select_all** | Select the entire image |
| **select_none** | Clear all selections |
| **select_invert** | Invert the current selection |
| **select_grow** | Expand selection by pixel radius |
| **select_shrink** | Shrink selection by pixel radius |

### Transforms (11 tools)
| Tool | Description |
|------|-------------|
| **scale_image** | Scale the entire image to new dimensions |
| **scale_layer** | Scale a single layer |
| **rotate_image** | Rotate image 90°, 180°, or 270° |
| **rotate_layer** | Rotate a layer by any angle |
| **flip_image** | Flip image horizontal or vertical |
| **flip_layer** | Flip a single layer |
| **crop_image** | Crop to a specific rectangle |
| **crop_to_selection** | Crop to the current selection bounds |
| **autocrop_image** | Auto-trim unused canvas around content |
| **resize_canvas** | Resize the canvas without scaling content |
| **offset_layer** | Reposition a layer on the canvas |

### Color Adjustments (13 tools)
| Tool | Description |
|------|-------------|
| **adjust_brightness_contrast** | Brightness and contrast (-127 to 127) |
| **adjust_hue_saturation** | Hue rotation, saturation, and lightness |
| **adjust_levels** | Input/output levels with gamma control |
| **adjust_curves** | Custom tone curves with control points |
| **desaturate** | Convert to grayscale (luminosity, average, lightness, luminance) |
| **invert_colors** | Negative/invert effect |
| **apply_threshold** | Convert to pure black and white |
| **posterize** | Reduce color levels for poster effect |
| **color_to_alpha** | Make a specific color transparent |
| **auto_white_balance** | Automatic levels stretch |
| **get_colors** | Get current foreground and background colors |
| **swap_colors** | Swap foreground and background colors |
| **sample_color** | Pick/sample a color from any pixel |

### Filters & Effects (8 tools)
| Tool | Description |
|------|-------------|
| **apply_gaussian_blur** | Gaussian blur with adjustable radius |
| **apply_unsharp_mask** | Sharpen with unsharp mask |
| **apply_pixelize** | Pixelization/mosaic effect |
| **apply_edge_detect** | Edge detection (Sobel, Prewitt, or Laplace) |
| **apply_emboss** | Emboss/relief effect with light angle control |
| **apply_noise** | Add random noise/film grain |
| **apply_median** | Median denoise filter |
| **apply_drop_shadow** | Drop shadow with offset, blur, and color |

### Inspection (4 tools)
| Tool | Description |
|------|-------------|
| **get_image_bitmap** | Get the image as a viewable PNG — lets Claude see what it's drawing |
| **get_image_metadata** | Fast metadata retrieval (no pixel data) |
| **get_context_state** | Current colors, brush, opacity, and settings |
| **get_gimp_info** | GIMP version, environment, and capabilities |

### History (3 tools)
| Tool | Description |
|------|-------------|
| **begin_undo_group** | Group multiple operations as a single undo step |
| **end_undo_group** | End the current undo group |
| **edit_clear** | Clear the selection to transparent |

### Advanced (2 tools)
| Tool | Description |
|------|-------------|
| **search_pdb** | Search GIMP's procedure database (thousands of operations) |
| **execute_python** | Run raw Python code in GIMP's console — the escape hatch |

### Key Features
- **Visual verification**: Claude can see the image after each step via `get_image_bitmap`
- **Pydantic validation**: All inputs validated before reaching GIMP
- **Length-prefixed framing**: Reliable TCP communication (no more JSON boundary guessing)
- **Persistent connections**: One TCP socket, kept alive, with automatic reconnection
- **Undo groups**: Multi-step AI workflows as a single Ctrl+Z
- **Color flexibility**: Accept names (`"red"`), hex (`"#FF0000"`), or CSS rgb (`"rgb(255,0,0)"`)
- **Font mapping**: Common font names automatically mapped to GIMP 3.0 equivalents
- **AI guidance prompts**: Built-in best practices and workflow documentation

---

## 🏗️ Architecture

```
Claude Desktop  ←→  MCP Server (gimp-mcp-pro)  ←→  GIMP Plugin
                      stdio transport                TCP socket
                      Typed tools                    PyGObject/GI
                      Pydantic models                Length-prefixed JSON
```

Two processes:
1. **MCP Server** — runs outside GIMP, handles Claude communication via stdio, validates inputs with Pydantic
2. **GIMP Plugin** — runs inside GIMP's Python process, executes commands via PyGObject API

They communicate over TCP with 4-byte big-endian length-prefixed JSON messages. This eliminates the fragile JSON boundary detection that caused reliability issues in earlier implementations.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **GIMP 3.0+** ([download](https://www.gimp.org/downloads/))
- **Claude Desktop**

### 1. Clone & Install

```bash
git clone https://github.com/Hackerobi/gimp-mcp-pro.git
cd gimp-mcp-pro
pip install -e .
```

Or use the setup script (installs both MCP server and GIMP plugin):

```bash
chmod +x setup.sh
./setup.sh
```

### 2. Install the GIMP Plugin

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

### 3. Start the Plugin in GIMP

Open GIMP → **Tools** → **Start MCP Pro Server**

You should see `MCP Pro: Listening on localhost:9877` in the GIMP console.

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

### 5. Restart Claude Desktop

The GIMP tools will appear automatically. Start creating.

---

## 🔑 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GIMP_MCP_HOST` | `localhost` | GIMP plugin socket host |
| `GIMP_MCP_PORT` | `9877` | GIMP plugin socket port |
| `GIMP_MCP_TIMEOUT` | `30` | Default command timeout (seconds) |
| `GIMP_MCP_LOG_LEVEL` | `INFO` | Logging level |
| `GIMP_MCP_DEBUG` | `false` | Enable debug mode |

---

## 💡 Usage Examples

### Create and Export
> "Create a 1920x1080 image with a dark blue background, add white text saying 'Presentation Title' centered, and export as PNG"

Claude chains: `create_image` → `fill_selection` → `add_text` → `export_image`

### Photo Editing
> "Take this image and increase the contrast, desaturate it, then add a slight gaussian blur for a moody effect"

Claude chains: `adjust_brightness_contrast` → `desaturate` → `apply_gaussian_blur`

### Layer Composition
> "Create three layers — a red circle on the bottom, a blue square in the middle at 50% opacity, and green text on top"

Claude chains: `create_layer` × 3 → `draw_ellipse` → `draw_rectangle` → `set_layer_opacity` → `add_text`

### Iterative Design
> "Show me what the image looks like, then make the background darker and add a drop shadow to the text"

Claude uses `get_image_bitmap` to see the current state, then applies changes and verifies again.

### Batch Operations with Undo Groups
> "Group these changes as one undo step: resize to 800x600, sharpen, and add a watermark"

Claude wraps with `begin_undo_group` → operations → `end_undo_group` so you can Ctrl+Z the whole thing.

---

## 🔧 Technical Notes

### Filter Implementation
All filters use `Gimp.DrawableFilter` which safely wraps GEGL operations within GIMP's plugin context. Direct GEGL graph construction (`Gegl.Node()`) crashes in GIMP 3.0 plugin context — GIMP MCP Pro works around this known limitation.

### Color Handling
Colors are accepted as names (`"red"`), hex (`"#FF0000"`), or CSS rgb (`"rgb(255,0,0)"`) across all 67 tools. Internally, colors use `Gegl.Color` objects with the GIMP 3.0 API.

### Font Handling
GIMP 3.0 uses `Gimp.Font` objects instead of string font names. The `add_text` tool automatically maps common aliases:
- `Sans` → `Sans-serif`
- `Mono` / `Monospace` → `Monospace`
- `Serif` → `Serif`

---

## ⚠️ Known Limitations

- **Undo/Redo**: GIMP 3.0's plugin API does not expose programmatic undo/redo. Use `Ctrl+Z` / `Ctrl+Y` in GIMP directly. Undo *groups* (begin/end) work for grouping AI operations.
- **Drop Shadow**: Uses Script-Fu internally and may cause connection issues on some setups. The shadow is applied successfully but the connection may need to reconnect.
- **Plugin context**: Some GEGL operations that work in Script-Fu console crash when run from a plugin. All 67 tools have been tested and verified to work from the plugin context.

---

## 📁 Project Structure

```
gimp-mcp-pro/
├── src/gimp_mcp_pro/
│   ├── server.py              # MCP server entry point
│   ├── bridge.py              # TCP bridge to GIMP plugin
│   ├── config.py              # Environment-based configuration
│   ├── models/                # Pydantic validation models
│   │   ├── common.py          # OperationResult, base models
│   │   ├── drawing.py         # Drawing parameter models
│   │   ├── image.py           # Image parameter models
│   │   ├── layer.py           # Layer parameter models
│   │   └── selection.py       # Selection parameter models
│   ├── tools/                 # 67 MCP tools across 10 modules
│   │   ├── image_tools.py     # Image management (6 tools)
│   │   ├── layer_tools.py     # Layer operations (9 tools)
│   │   ├── drawing_tools.py   # Drawing and text (9 tools)
│   │   ├── selection_tools.py # Selections (8 tools)
│   │   ├── transform_tools.py # Transforms and crop (11 tools)
│   │   ├── color_tools.py     # Color adjustments (13 tools)
│   │   ├── filter_tools.py    # Filters and effects (8 tools)
│   │   ├── inspect_tools.py   # Inspection (4 tools)
│   │   ├── history_tools.py   # Undo groups (3 tools)
│   │   └── pdb_tools.py       # PDB search and execute (2 tools)
│   ├── prompts/               # AI guidance documentation
│   │   ├── api_reference.md   # GIMP 3.0.8 API quick reference
│   │   ├── best_practices.md  # Drawing best practices
│   │   ├── filter_catalog.md  # Available filters and parameters
│   │   └── iterative_workflow.md  # Verification workflow guide
│   └── utils/                 # Shared utilities
│       ├── errors.py          # Custom exception hierarchy
│       ├── gimp_constants.py  # GIMP enum mappings
│       └── logging.py         # Logging configuration
├── gimp_plugin/
│   └── gimp_mcp_plugin.py     # GIMP-side plugin (runs inside GIMP)
├── tests/                     # Test suite
├── pyproject.toml             # Python packaging (hatchling)
├── setup.sh                   # One-command installer
├── CHANGELOG.md
├── LICENSE
└── README.md
```

---

## 🧪 Development

```bash
git clone https://github.com/Hackerobi/gimp-mcp-pro.git
cd gimp-mcp-pro
pip install -e ".[dev]"
pytest -v
```

---

## 🏗️ Built With

- **[GIMP 3.0](https://www.gimp.org/)** — GNU Image Manipulation Program
- **[MCP SDK](https://github.com/modelcontextprotocol/python-sdk)** — Model Context Protocol Python SDK
- **[Pydantic](https://docs.pydantic.dev/)** — Data validation
- **[PyGObject](https://pygobject.gnome.org/)** — GIMP's Python bindings (GObject Introspection)

Built on insights from:
- [maorcc/gimp-mcp](https://github.com/maorcc/gimp-mcp) — proven GIMP plugin architecture, AI guidance prompts
- [slliws/gimp-mcp-server](https://github.com/slliws/gimp-mcp-server) — typed tool module structure
- [libreearth/gimp-mcp](https://github.com/libreearth/gimp-mcp) — original proof-of-concept

---

## 🤝 Contributing

Pull requests welcome. To add a new tool:

1. Add the function in the appropriate `tools/*.py` module with the `@mcp.tool()` decorator
2. Add a Pydantic input model in `models/` if needed
3. Test against a running GIMP instance
4. Update this README
5. Submit a PR

---

## 📬 Contact

- **Discord:** sgtwolf787
- **GitHub:** [@Hackerobi](https://github.com/Hackerobi)

White hat or no hat 🎩

---

*Built with Claude. Tested on GIMP 3.0.8 with 67 tools verified. Create something cool.*
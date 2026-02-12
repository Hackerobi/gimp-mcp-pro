# GIMP MCP Pro — GIMP 3.0.8 API Quick Reference

## Working Methods (Verified on GIMP 3.0.8)

```python
# Images
Gimp.get_images()              # Returns list of open images
image.get_width() / image.get_height()
image.get_layers()
image.get_selected_layers()    # Returns list (GIMP 3.0 replaces get_active_layer)
image.get_layer_by_name(name)
image.get_base_type()

# Layers
Gimp.Layer.new(image, name, width, height, type, opacity, mode)
image.insert_layer(layer, parent, position)
image.remove_layer(layer)
layer.get_name() / layer.set_name(name)
layer.get_visible() / layer.set_visible(bool)
layer.get_opacity() / layer.set_opacity(float)
layer.get_mode() / layer.set_mode(mode)
layer.has_alpha() / layer.add_alpha()
layer.get_width() / layer.get_height()
layer.get_offsets()            # Returns ResultTuple(True, offset_x=N, offset_y=N)
layer.set_offsets(x, y)
layer.copy()

# Colors
Gegl.Color.new('red')         # Named colors
Gegl.Color.new('#FF0000')     # Hex colors
Gimp.context_set_foreground(color)
Gimp.context_set_background(color)
Gimp.context_get_foreground()  # Returns Gegl.Color
Gimp.context_get_background()  # Returns Gegl.Color
Gimp.context_swap_colors()
# Extracting RGBA from Gegl.Color:
rgba = color.get_rgba()        # Returns ResultTuple with .red .green .blue .alpha (0-1 floats)

# Fonts (GIMP 3.0)
Gimp.Font.get_by_name('Sans-serif')  # Returns Gimp.Font or None
Gimp.context_get_font()              # Returns current context font (always valid)
# Common GIMP 3.0 font names: 'Sans-serif', 'Serif', 'Monospace'

# Text Layers
Gimp.TextLayer.new(image, text, font_obj, size, Gimp.Unit.pixel())
# font_obj must be a Gimp.Font object, NOT a string

# Selections
Gimp.Image.select_rectangle(image, op, x, y, width, height)
Gimp.Image.select_ellipse(image, op, x, y, width, height)
Gimp.Image.select_polygon(image, op, points_flat_list)
Gimp.Selection.all(image)
Gimp.Selection.none(image)
Gimp.Selection.invert(image)
Gimp.Selection.grow(image, radius)
Gimp.Selection.shrink(image, radius, False)
Gimp.Selection.bounds(image)   # Returns ResultTuple(True, non_empty=T, x1=N, y1=N, x2=N, y2=N)

# Drawing
Gimp.pencil(drawable, points)
Gimp.paintbrush_default(drawable, points)
Gimp.Drawable.edit_fill(drawable, fill_type)
Gimp.Drawable.edit_clear(drawable)
Gimp.Drawable.edit_stroke_selection(drawable)

# Filters (SAFE pattern for GIMP 3.0 plugins)
df = Gimp.DrawableFilter.new(drawable, 'gegl:gaussian-blur', '')
cfg = df.get_config()
cfg.set_property('std-dev-x', 5.0)
drawable.append_filter(df)
drawable.merge_filter(df)
# WARNING: Direct Gegl.Node() construction crashes in plugin context!

# Color Adjustments
Gimp.Drawable.desaturate(drawable, Gimp.DesaturateMode.LUMA)
Gimp.Drawable.invert(drawable, False)  # Second arg = linear (boolean)
Gimp.Drawable.threshold(drawable, Gimp.HistogramChannel.VALUE, low, high)
Gimp.Drawable.posterize(drawable, levels)
Gimp.Drawable.levels_stretch(drawable)

# Transforms
Gimp.Item.transform_rotate(layer, angle_rad, auto_resize, cx, cy)
Gimp.Item.transform_flip_simple(layer, flip_type, auto_center, axis)

# File I/O (via PDB)
pdb = Gimp.get_pdb()
proc = pdb.lookup_procedure('file-png-export')
config = proc.create_config()
config.set_property('image', image)
config.set_property('file', Gio.File.new_for_path('/path/to/file.png'))
proc.run(config)

# Display
Gimp.Display.new(image)
Gimp.displays_flush()         # REQUIRED after drawing operations

# Undo Groups
image.undo_group_start()
image.undo_group_end()
# Note: Programmatic undo/redo not available in GIMP 3.0 plugin API
```

## DEPRECATED / DOES NOT EXIST in GIMP 3.0.8

```python
# DO NOT USE:
Gimp.get_active_image()           # Does not exist
Gimp.get_active_layer()           # Use image.get_selected_layers()
from gimpfu import *              # gimpfu module not available
Gimp.file_new_for_path()          # Use Gio.File.new_for_path()
Gimp.list_images()                # Use Gimp.get_images()
Gimp.Unit.PIXEL()                 # Use Gimp.Unit.pixel() (lowercase)
Gimp.DesaturateMode.LUMINOSITY    # Does not exist — use LUMA
Gimp.Image.undo(image)            # Does not exist in plugin context
Gimp.Image.redo(image)            # Does not exist in plugin context
Gimp.Item.transform_rotate_default()  # Use transform_rotate()
Gegl.Node()                       # Crashes in plugin context — use DrawableFilter
color.get_rgba().r                # Wrong — use color.get_rgba().red
```

## Required Imports

```python
from gi.repository import Gimp, Gegl    # Always needed
from gi.repository import Gio            # For file operations
```

## Common Enums

```python
# Image types
Gimp.ImageType.RGBA_IMAGE      # Most common for new layers

# Fill types
Gimp.FillType.FOREGROUND / BACKGROUND / WHITE / TRANSPARENT / PATTERN

# Selection operations
Gimp.ChannelOps.REPLACE / ADD / SUBTRACT / INTERSECT

# Desaturation
Gimp.DesaturateMode.LUMA / AVERAGE / LIGHTNESS / LUMINANCE / VALUE

# GEGL filter names (for DrawableFilter)
# gegl:gaussian-blur (std-dev-x, std-dev-y)
# gegl:unsharp-mask (std-dev, scale, threshold)
# gegl:pixelize (size-x, size-y)
# gegl:edge (algorithm, amount)
# gegl:edge-laplace (no params)
# gegl:emboss (azimuth, elevation, depth)
# gegl:noise-hsv (holdness, value-distance)
# gegl:median-blur (radius)
# gegl:color-to-alpha (color)
```

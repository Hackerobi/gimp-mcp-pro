# GIMP MCP Pro — Best Practices

## Filling Shapes — The Right Way

**DO: Use selection + fill for solid shapes**
```
select_polygon(points=[x1,y1, x2,y2, x3,y3, ...])
fill_selection(color="red")
select_none()
```

**DON'T: Use paintbrush for filling areas**
Paintbrush creates thin strokes along a path — not solid fills.

**For rectangles and ellipses, use the dedicated tools:**
```
draw_rectangle(x=10, y=10, width=200, height=100, filled=True, color="blue")
draw_ellipse(x=50, y=50, width=100, height=100, filled=True, color="green")
```

## Feathering — Use Sparingly

- Use sharp edges by default (feather_radius=0)
- Only add feathering for: soft shadows, blending, glow effects
- Feathered edges look blurry and unprofessional unless intentional
- If something looks cloudy/blurry, check if feathering was accidentally enabled

## Layer Workflow

**Always create layers BEFORE drawing.** Plan your structure:
1. Background layer (sky, ground, base color)
2. Main subject layer(s) (body, objects)
3. Detail layers (face features, text, fine elements)
4. Effect layers (shadows, highlights, texture overlays)

**Switch layers before drawing:**
```
set_active_layer(layer_name="Eyes")
# Now drawing operations target the Eyes layer
```

## Variable Persistence

GIMP's Python console maintains state between execute_python calls:
- Imports persist — no need to re-import
- Variables persist — initialize once, reuse many times
- Functions persist — define helpers once

## Undo Groups

Wrap multi-step operations in undo groups so the user can revert with one Ctrl+Z:
```
begin_undo_group(name="Draw face")
# ... multiple drawing operations ...
end_undo_group()
```

## Color Verification

The user can change colors in GIMP's UI at any time. Before drawing:
```
get_context_state()  # Verify current foreground/background colors
set_foreground_color(color="red")  # Explicitly set what you need
```

## After Every Drawing Operation

1. Always call `Gimp.displays_flush()` (typed tools do this automatically)
2. Always clear selections after fill/stroke operations (typed tools do this automatically)
3. Verify results with `get_image_bitmap()` after every 3-5 operations

## Self-Critique Checklist

After viewing with `get_image_bitmap()`:
- [ ] Do shapes match their intended form?
- [ ] Are edges sharp and clean (not blurry)?
- [ ] Are colors correct?
- [ ] Are elements on the correct layers?
- [ ] Were all selections cleared?
- [ ] Are there unwanted artifacts?

**If issues found: STOP. Fix on the correct layer. Validate again. Never paint over problems.**

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Blurry/cloudy edges | Remove feathering — use feather_radius=0 |
| Missing elements | Check you drew on the right layer |
| Wrong colors | Call set_foreground_color explicitly before drawing |
| Rectangular artifacts | Call select_none() to clear leftover selections |
| Painting over problems | Use undo, fix on correct layer, validate |

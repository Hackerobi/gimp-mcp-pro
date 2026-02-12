# GIMP MCP Pro — Iterative Workflow

## The Golden Rule

**Check your work with get_image_bitmap() after every 3-5 operations. Don't continue blindly.**

## Phase-Based Workflow

### Phase 1: Planning (Before Drawing Anything)

1. Check what you're working with:
   ```
   get_image_metadata()  → canvas size, existing layers
   get_context_state()   → current colors, brush settings
   ```

2. Plan your layer structure. Example for drawing an animal:
   - background_layer: sky and ground
   - body_layer: main body and legs
   - head_layer: head and ears
   - details_layer: eyes, nose, facial features

### Phase 2: Layer Setup

Create ALL layers BEFORE drawing:
```
create_layer(name="Background", fill="white", position=3)
create_layer(name="Body", fill="transparent", position=2)
create_layer(name="Head", fill="transparent", position=1)
create_layer(name="Details", fill="transparent", position=0)
```

### Phase 3: Incremental Drawing with Validation

**The Pattern:**
1. Set active layer
2. Draw 3-5 elements
3. Validate with get_image_bitmap()
4. Review and fix issues
5. Repeat

**Example:**
```
# Step 1: Draw body
set_active_layer(layer_name="Body")
draw_ellipse(x=100, y=200, width=200, height=150, color="brown")
# ... more body operations ...

# Step 2: VALIDATE (critical!)
get_image_bitmap(max_width=1024, max_height=1024)
# STOP and analyze what you see. Compare to intent.

# Step 3: Fix issues if any (on correct layer!)
# Only continue when current phase looks right.

# Step 4: Next layer
set_active_layer(layer_name="Head")
draw_ellipse(x=200, y=150, width=80, height=80, color="brown")

# Step 5: VALIDATE again
get_image_bitmap(max_width=1024, max_height=1024)
```

### Phase 4: Detail and Polish

- Use get_image_bitmap with region parameters to check specific areas at higher quality
- Work on detail layers for fine elements
- Consider using undo groups for experimental changes

## Regional Verification

For checking specific areas at higher quality:
```
get_image_bitmap(
    region_x=100, region_y=50,
    region_width=200, region_height=200,
    max_width=512, max_height=512
)
```

## Fixing Mistakes

### DO:
- Identify which layer has the problem
- Switch to that layer: `set_active_layer(layer_name="...")`
- Clear the problem area: `select_rectangle(...)` then `edit_clear()`
- Redraw correctly
- Validate the fix

### DON'T:
- Paint over problems (creates more mess)
- Continue when something looks wrong
- Skip validation "to save time"
- Fix on the wrong layer

## Layer Management Tips

- Use `list_layers()` to see what's where
- Use `set_layer_visibility(visible=False)` to isolate layers for inspection
- Use `set_layer_opacity()` for blending effects
- Group related operations with `begin_undo_group()` / `end_undo_group()`

## Summary

Work like a professional digital artist:
1. **Plan** layer structure first
2. **Build** incrementally (3-5 ops at a time)
3. **Validate** after each build phase
4. **Fix** issues immediately on correct layer
5. **Continue** only when current phase is correct

**Don't treat GIMP like a single canvas — leverage layers!**

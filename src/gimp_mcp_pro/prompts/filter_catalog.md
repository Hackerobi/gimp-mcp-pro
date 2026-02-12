# GIMP MCP Pro — Filter & Effect Catalog

## Blur Filters

### Gaussian Blur (`apply_gaussian_blur`)
- **Use for:** Softening, depth-of-field, background blur, noise smoothing
- **Key params:** radius_x (0-500), radius_y (0-500, defaults to radius_x)
- **Tips:** Radius 1-3 = subtle smoothing, 5-15 = noticeable blur, 20+ = heavy blur

### Median Filter (`apply_median`)
- **Use for:** Removing salt-and-pepper noise while keeping edges sharp
- **Key params:** radius (1-20)
- **Tips:** Better than Gaussian for denoising while preserving edges

## Sharpening

### Unsharp Mask (`apply_unsharp_mask`)
- **Use for:** Enhancing detail, post-resize sharpening, focus recovery
- **Key params:** amount (0-5, typical 0.3-1.0), radius (0.1-120, typical 1-5), threshold (0-1)
- **Tips:** High amount + low radius = fine detail, Low amount + high radius = overall contrast

## Noise

### HSV Noise (`apply_noise`)
- **Use for:** Film grain, texture, breaking smooth gradients
- **Key params:** amount (0-1)
- **Tips:** Use sparingly — 0.05-0.15 for subtle grain

## Edge Detection

### Edge Detect (`apply_edge_detect`)
- **Use for:** Artistic outlines, contour finding, line-art from photos
- **Key params:** method ("sobel"/"prewitt"/"laplace"), amount (0-10)
- **Tips:** Sobel = most common, Laplace = more detail

## Artistic Effects

### Pixelize (`apply_pixelize`)
- **Use for:** Censoring, retro pixel effect, privacy masking
- **Key params:** block_width (1-1024), block_height (defaults to block_width)

### Emboss (`apply_emboss`)
- **Use for:** Raised/carved look, metallic textures
- **Key params:** azimuth (0-360, light direction), elevation (0-180), depth (1-100)

### Drop Shadow (`apply_drop_shadow`)
- **Use for:** Adding depth, making elements stand out from background
- **Key params:** offset_x, offset_y, blur_radius, color, opacity

## Color Adjustments

### Brightness/Contrast (`adjust_brightness_contrast`)
- **Use for:** Quick overall lightness/contrast tweaks
- **Range:** -127 to 127 each

### Hue/Saturation (`adjust_hue_saturation`)
- **Use for:** Color shifts, vibrancy adjustment, color grading
- **Range:** Hue ±180°, Saturation ±100, Lightness ±100

### Levels (`adjust_levels`)
- **Use for:** Tonal range correction, fixing exposure
- **Key concept:** Input range maps to output range with gamma curve

### Curves (`adjust_curves`)
- **Use for:** Fine-grained tonal control, S-curves for contrast
- **Input:** Control points as [in1,out1, in2,out2, ...] (0.0-1.0)
- **Classic S-curve:** [0,0, 0.25,0.15, 0.5,0.5, 0.75,0.85, 1,1]

### Desaturate (`desaturate`)
- **Use for:** Converting to grayscale while staying in RGB mode
- **Methods:** "luminosity" (perceptual, best default), "average", "lightness"

### Color to Alpha (`color_to_alpha`)
- **Use for:** Background removal, making white/black transparent
- **Tips:** Works best on solid-color backgrounds

### Auto White Balance (`auto_white_balance`)
- **Use for:** Quick automatic color/exposure correction

### Threshold (`apply_threshold`)
- **Use for:** Pure black & white conversion

### Posterize (`posterize`)
- **Use for:** Reducing colors for artistic effect, poster-style graphics

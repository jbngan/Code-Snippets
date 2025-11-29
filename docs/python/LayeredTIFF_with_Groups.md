# Creating Multi-Layered TIFF Files with PSD Layer Groups using psdtags

## Overview

This guide explains how to create layered TIFF files with Photoshop-compatible layer groups using the `psdtags` library. These files can be opened in Adobe Photoshop with full layer structure preserved, including layer groups (folders). This is useful for programmatically generating complex layered images with organized layer hierarchies.

## Requirements

```bash
pip install psdtags
pip install tifffile
pip install numpy
pip install Pillow
```

## Key Concepts

### PSD Layer Structure

In Photoshop's PSD format, layer groups are created using special divider layers with section divider settings:

- **Group Folder Layer**: Marks the beginning of a group (OPEN_FOLDER or CLOSED_FOLDER)
- **Group Content Layers**: The actual layers inside the group
- **Bounding Divider Layer**: Marks the end of the group (BOUNDING_SECTION_DIVIDER)

### Critical Layer Ordering

The correct order for layer groups in the PSD layers array is **bottom-to-top** (reversed from visual appearance):

```
Layers Array Order (bottom-to-top):
┌─────────────────────────────────┐
│ 1. Bounding Divider             │  ← End marker (BOUNDING_SECTION_DIVIDER)
│ 2. Last Item (reversed order)   │  ← Group content (bottom-most in Photoshop)
│ 3. ...                          │  ← Group content
│ 4. First Item (reversed order)  │  ← Group content (top-most in Photoshop)
│ 5. Group Folder                 │  ← Start marker (OPEN_FOLDER)
│ 6. Additional Layer (if any)    │  ← Outside the group
└─────────────────────────────────┘
```

**Visual in Photoshop (top-to-bottom):**
```
Layers Panel:
┌─────────────────────────────────┐
│ Background                      │  ← Outside group
│ ▼ Items (Group)                 │  ← Group folder (expanded)
│   ├─ Item #1                    │  ← First item
│   ├─ Item #2                    │
│   ├─ ...                        │
│   └─ Item #36                   │  ← Last item
└─────────────────────────────────┘
```

## Code Implementation

### 1. Import Required Libraries

```python
import numpy as np
from PIL import Image, ImageDraw
from psdtags import (
    TiffImageSourceData, PsdFormat, PsdLayers, PsdLayer, PsdRectangle,
    PsdChannel, PsdChannelId, PsdCompressionType, PsdLayerMask,
    PsdBlendMode, PsdClippingType, PsdLayerFlag, PsdString, PsdKey,
    PsdUserMask, PsdColorSpaceType, PsdSectionDividerSetting,
    PsdSectionDividerType
)
from tifffile import imwrite as tiff_imwrite
```

### 2. Create Individual Layer Function

```python
def create_psd_layer(image, layer_name, x, y, width, height):
    """
    Create a PSD layer from a PIL Image.

    Args:
        image: PIL Image in RGBA mode
        layer_name: Name of the layer
        x, y: Position in pixels (top-left origin)
        width, height: Size in pixels

    Returns:
        PsdLayer object
    """
    # Convert PIL Image to numpy array
    img_array = np.array(image)

    # Extract RGBA channels
    r_channel = img_array[:, :, 0]
    g_channel = img_array[:, :, 1]
    b_channel = img_array[:, :, 2]
    a_channel = img_array[:, :, 3]

    # Create PSD channels
    channels = [
        PsdChannel(
            channelid=PsdChannelId.TRANSPARENCY_MASK,
            compression=PsdCompressionType.RLE,
            data=a_channel,
        ),
        PsdChannel(
            channelid=PsdChannelId.CHANNEL0,
            compression=PsdCompressionType.RLE,
            data=r_channel,
        ),
        PsdChannel(
            channelid=PsdChannelId.CHANNEL1,
            compression=PsdCompressionType.RLE,
            data=g_channel,
        ),
        PsdChannel(
            channelid=PsdChannelId.CHANNEL2,
            compression=PsdCompressionType.RLE,
            data=b_channel,
        ),
    ]

    # Create PSD layer
    psd_layer = PsdLayer(
        name=layer_name,
        rectangle=PsdRectangle(y, x, y + height, x + width),  # top, left, bottom, right
        channels=channels,
        mask=PsdLayerMask(),
        opacity=255,
        blendmode=PsdBlendMode.NORMAL,
        blending_ranges=(),
        clipping=PsdClippingType.BASE,
        flags=PsdLayerFlag.PHOTOSHOP5,
        info=[
            PsdString(PsdKey.UNICODE_LAYER_NAME, layer_name),
        ],
    )

    return psd_layer
```

### 3. Create Layer Group Structure

```python
def create_layer_group(group_name, item_layers, artboard_width, artboard_height):
    """
    Create a layer group with items inside.

    Args:
        group_name: Name of the group folder
        item_layers: List of PsdLayer objects to include in the group
        artboard_width: Total artboard width in pixels
        artboard_height: Total artboard height in pixels

    Returns:
        List of layers in correct order: [divider, reversed_items, group_folder]
    """
    # Create bounding divider layer (marks end of group)
    divider_layer = PsdLayer(
        name="</Layer group>",
        rectangle=PsdRectangle(0, 0, 0, 0),  # Empty rectangle
        channels=[],
        mask=PsdLayerMask(),
        opacity=255,
        blendmode=PsdBlendMode.PASS_THROUGH,
        blending_ranges=(),
        clipping=PsdClippingType.BASE,
        flags=PsdLayerFlag.PHOTOSHOP5,
        info=[
            PsdSectionDividerSetting(
                kind=PsdSectionDividerType.BOUNDING_SECTION_DIVIDER,
                blendmode=PsdBlendMode.PASS_THROUGH
            ),
        ],
    )

    # Create group folder layer (marks start of group)
    group_layer = PsdLayer(
        name=group_name,
        rectangle=PsdRectangle(0, 0, artboard_height, artboard_width),
        channels=[],
        mask=PsdLayerMask(),
        opacity=255,
        blendmode=PsdBlendMode.PASS_THROUGH,
        blending_ranges=(),
        clipping=PsdClippingType.BASE,
        flags=PsdLayerFlag.PHOTOSHOP5,
        info=[
            PsdString(PsdKey.UNICODE_LAYER_NAME, group_name),
            PsdSectionDividerSetting(
                kind=PsdSectionDividerType.OPEN_FOLDER,
                blendmode=PsdBlendMode.PASS_THROUGH
            ),
        ],
    )

    # Return layers in correct order: Divider → Items (reversed) → Group
    group_layers = []
    group_layers.append(divider_layer)
    group_layers.extend(reversed(item_layers))  # CRITICAL: Reverse the item order
    group_layers.append(group_layer)

    return group_layers
```

### 4. Create Layered TIFF File

```python
def create_layered_tiff_with_groups(output_file, width_px, height_px, dpi=300):
    """
    Create a layered TIFF file with layer groups.

    Args:
        output_file: Path to save the TIFF file
        width_px: Artboard width in pixels
        height_px: Artboard height in pixels
        dpi: Resolution in dots per inch (default: 300)
    """
    # Create base transparent image (RGBA)
    base_img = np.zeros((height_px, width_px, 4), dtype=np.uint8)

    # Create item layers
    item_layers = []

    # Example: Create 3 colored rectangles as layers
    for i in range(3):
        # Create a PIL image for this layer
        layer_img = Image.new('RGBA', (200, 200),
                              (255 * (i % 2), 255 * ((i+1) % 2), 255 * ((i+2) % 2), 255))

        # Position on artboard
        x = 100 + (i * 250)
        y = 100

        # Create full-size canvas and paste layer image
        full_canvas = Image.new('RGBA', (width_px, height_px), (0, 0, 0, 0))
        full_canvas.paste(layer_img, (x, y), layer_img)

        # Create PSD layer
        psd_layer = create_psd_layer(
            full_canvas,
            f"Item_{i+1}",
            0, 0,
            width_px, height_px
        )
        item_layers.append(psd_layer)

    # Create layer group
    group_layers = create_layer_group("Items", item_layers, width_px, height_px)

    # Combine all layers
    all_layers = []
    all_layers.extend(group_layers)  # Add grouped items

    # Optional: Add additional layers outside the group (e.g., background layer)
    # background_layer = create_psd_layer(background_img, "Background", 0, 0, width_px, height_px)
    # all_layers.append(background_layer)

    # Create TIFF image source data
    image_source_data = TiffImageSourceData(
        name='Layered_TIFF_with_Groups',
        psdformat=PsdFormat.LE32BIT,
        layers=PsdLayers(
            key=PsdKey.LAYER,
            has_transparency=True,
            layers=all_layers,
        ),
        usermask=PsdUserMask(
            colorspace=PsdColorSpaceType.RGB,
            components=(0, 0, 0, 0),
            opacity=0,
        ),
    )

    # Write layered TIFF file
    tiff_imwrite(
        output_file,
        base_img,
        compression='lzw',
        photometric='rgb',
        resolution=(dpi, dpi),
        resolutionunit=2,  # 2 = inches
        extratags=[image_source_data.tifftag()],
    )

    print(f"Created layered TIFF with {len(all_layers)} layers: {output_file}")
```

### 5. Usage Example

```python
# Create a layered TIFF with groups
create_layered_tiff_with_groups(
    output_file="output/layered_with_groups.tif",
    width_px=1000,
    height_px=1000,
    dpi=300
)
```

## Important Notes

### Layer Ordering

⚠️ **Critical**: The layer order must follow this exact pattern:
1. Bounding divider (BOUNDING_SECTION_DIVIDER)
2. Items in **reversed** order (last item first)
3. Group folder (OPEN_FOLDER)

Any other order will result in corrupted files or improper grouping.

### Blend Modes

- Use `PsdBlendMode.PASS_THROUGH` for group layers and dividers
- Use `PsdBlendMode.NORMAL` for regular content layers

### Rectangle Coordinates

- PsdRectangle uses format: `(top, left, bottom, right)`
- Coordinates are in pixels with top-left origin (y=0 at top)
- Group layer rectangle should span the full artboard: `PsdRectangle(0, 0, height, width)`
- Divider layer uses empty rectangle: `PsdRectangle(0, 0, 0, 0)`

### Layer Flags

- Regular layers: `PsdLayerFlag.PHOTOSHOP5`
- Group/divider layers: `PsdLayerFlag.PHOTOSHOP5`
- No HIDDEN flag available in psdtags

### Channel Order

Channels must be in this exact order:
1. Transparency mask (TRANSPARENCY_MASK)
2. Red channel (CHANNEL0)
3. Green channel (CHANNEL1)
4. Blue channel (CHANNEL2)

## Testing

To verify your implementation works correctly:

1. Open the generated TIFF file in Adobe Photoshop
2. Check the Layers panel:
   - Verify the group folder appears
   - Verify all items are inside the group
   - Verify layers outside the group (if any) are at the correct level
3. Expand/collapse the group to ensure it functions properly
4. Check for corruption warnings

## Troubleshooting

### File Corruption
- **Cause**: Incorrect layer ordering
- **Solution**: Ensure correct ordering (Divider → Reversed Items → Group)

### Layers Not in Group
- **Cause**: Missing section divider settings or incorrect divider type
- **Solution**: Verify PsdSectionDividerSetting with correct `kind` parameter

### Group Not Visible
- **Cause**: Using CLOSED_FOLDER instead of OPEN_FOLDER
- **Solution**: Use `PsdSectionDividerType.OPEN_FOLDER` for the group layer

### Incorrect Layer Order in Photoshop
- **Cause**: Forgot to reverse item layers
- **Solution**: Use `reversed(item_layers)` when adding to psd_layers

## References

- **psdtags Documentation**: [https://github.com/cgohlke/psdtags](https://github.com/cgohlke/psdtags)
- **Adobe PSD Format Specification**: Available from Adobe

## Version History

- **2025-11-29**: Initial documentation
- Discovered correct layer ordering through systematic testing

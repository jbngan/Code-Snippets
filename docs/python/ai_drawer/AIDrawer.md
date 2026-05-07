# AIDrawer

`PyRender.core.ai_drawer` — helper class for drawing layered vector paths in Adobe Illustrator via Windows COM automation.

## Requirements

- Windows with Adobe Illustrator installed
- `pywin32` package (`pip install pywin32`)

---

## Constants

### Units

| Constant  | Value  | Description                        |
|-----------|--------|------------------------------------|
| `UNIT_PT` | `"pt"` | Points — Illustrator native (default) |
| `UNIT_MM` | `"mm"` | Millimetres                        |
| `UNIT_IN` | `"in"` | Inches                             |

### Coordinate systems

| Constant           | Value           | Description |
|--------------------|-----------------|-------------|
| `COORD_BOTTOM_LEFT` | `"bottom-left"` | Illustrator native: origin at bottom-left, Y increases upward (default) |
| `COORD_TOP_LEFT`    | `"top-left"`    | Screen / CSS convention: origin at top-left, Y increases downward |

---

## Class: `AIDrawer`

### Constructor

```python
AIDrawer(
    page_size=(612, 792),
    ruler_origin=(0, 0),
    unit=UNIT_PT,
    coord_system=COORD_BOTTOM_LEFT,
    layers=None
)
```

| Parameter      | Type            | Default             | Description |
|----------------|-----------------|---------------------|-------------|
| `page_size`    | `(w, h)`        | `(612, 792)`        | Document dimensions in the caller's unit |
| `ruler_origin` | `(x, y)`        | `(0, 0)`            | Offset applied to all path coordinates |
| `unit`         | `str`           | `UNIT_PT`           | Unit of measure for all caller values |
| `coord_system` | `str`           | `COORD_BOTTOM_LEFT` | Coordinate origin and Y direction |
| `layers`       | `list` or `None`| `None`              | Layer definitions (see below) |

All dimensional values — `page_size`, `ruler_origin`, path coordinates, widths, heights, and `stroke_width` — are interpreted in `unit` and converted to points internally.

---

### Methods

#### `draw() → doc`

Opens Illustrator (or connects to a running instance), creates a new document at `page_size`, and draws all layers. Returns the Illustrator document COM object.

Must be called before `save()` or `close()`.

---

#### `save(filename)`

Saves the document. The output format is inferred from the file extension.

| Extension | Format |
|-----------|--------|
| `.ai`     | Adobe Illustrator |
| `.pdf`    | PDF |
| `.eps`    | Encapsulated PostScript |
| `.svg`    | Scalable Vector Graphics |

Illustrator requires an absolute path; a relative path is resolved automatically via `os.path.abspath`.

Raises `RuntimeError` if called before `draw()`.  
Raises `ValueError` for unsupported extensions.

---

#### `close(save=False)`

Closes the document.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `save`    | `False` | If `True`, saves before closing. Requires a prior `save()` call to establish a file path. |

Safe to call even if `draw()` was never called (no-op).

---

## Layer definition

Each entry in `layers` is a `dict`:

```python
{
    "name":         str,        # Layer name as it appears in Illustrator
    "color":        (r, g, b),  # Stroke colour, 0–255 per channel. Default: (0, 0, 0)
    "stroke_width": float,      # Stroke width in the caller's unit. Default: 1 pt
    "paths":        [...]       # List of path dicts (see below)
}
```

---

## Path types

All coordinate values are in the caller's unit and relative to `ruler_origin`.

### `line`

Draws an open path through two or more points.

```python
{"type": "line", "points": [(x1, y1), (x2, y2), ...]}
```

### `rectangle`

Draws a rectangle.

```python
{"type": "rectangle", "left": n, "top": n, "width": n, "height": n}
```

`top` meaning depends on the coordinate system:
- `COORD_BOTTOM_LEFT` — the **higher** Y value (top edge in Y-up space)
- `COORD_TOP_LEFT` — distance **downward** from the origin to the top edge

### `ellipse`

Draws an ellipse inscribed in a bounding box.

```python
{"type": "ellipse", "left": n, "top": n, "width": n, "height": n}
```

Same `top` convention as `rectangle`.

---

## Coordinate systems in detail

### `COORD_BOTTOM_LEFT` (default)

Matches Illustrator's native scripting system. The origin `(0, 0)` is at the **bottom-left** of the artboard; Y increases upward.

```
(0, h) ─────────────── (w, h)   ← top of page
  │                        │
  │                        │
(0, 0) ─────────────── (w, 0)   ← bottom of page (origin)
```

Use this when coordinates come from Illustrator or are calculated in traditional math/print convention.

### `COORD_TOP_LEFT`

Screen and CSS convention. The origin `(0, 0)` is at the **top-left** of the artboard; Y increases downward.

```
(0, 0) ─────────────── (w, 0)   ← top of page (origin)
  │                        │
  │                        │
(0, h) ─────────────── (w, h)   ← bottom of page
```

Use this when coordinates come from image processing, UI layout, or other screen-space systems.

### `ruler_origin`

Offsets the drawing origin within the page. All path coordinates are relative to this point.

- With `COORD_BOTTOM_LEFT`: offset from the page bottom-left.
- With `COORD_TOP_LEFT`: offset from the page top-left.

Example: `ruler_origin=(10, 10)` with `UNIT_MM` adds a 10 mm margin on the left and top (or bottom in BL mode) before any path is drawn.

---

## Examples

### Millimetres, A4, top-left coordinates

```python
from PyRender.core.ai_drawer import AIDrawer, UNIT_MM, COORD_TOP_LEFT

layers = [
    {
        "name": "Cut lines",
        "color": (255, 0, 0),
        "stroke_width": 0.25,       # 0.25 mm
        "paths": [
            {"type": "line", "points": [(10, 10), (200, 10)]},
            {"type": "line", "points": [(10, 10), (10,  287)]},
        ],
    },
    {
        "name": "Design area",
        "color": (0, 0, 255),
        "stroke_width": 0.1,
        "paths": [
            {"type": "rectangle", "left": 10, "top": 10, "width": 190, "height": 277},
        ],
    },
]

drawer = AIDrawer(
    page_size=(210, 297),       # A4
    unit=UNIT_MM,
    coord_system=COORD_TOP_LEFT,
    layers=layers,
)
drawer.draw()
drawer.save("output.pdf")
drawer.close()
```

### Inches, US Letter, bottom-left coordinates

```python
from PyRender.core.ai_drawer import AIDrawer, UNIT_IN, COORD_BOTTOM_LEFT

layers = [
    {
        "name": "Border",
        "color": (0, 0, 0),
        "stroke_width": 0.01,       # 0.01 in ≈ 0.72 pt
        "paths": [
            # bottom-left at (0.5, 0.5), top-right at (8.0, 10.5)
            {"type": "rectangle", "left": 0.5, "top": 10.5, "width": 7.5, "height": 10.0},
        ],
    },
]

drawer = AIDrawer(
    page_size=(8.5, 11),
    unit=UNIT_IN,
    coord_system=COORD_BOTTOM_LEFT,
    layers=layers,
)
drawer.draw()
drawer.save("output.ai")
drawer.close()
```

### Using `ruler_origin` to add a margin

```python
# All paths are defined from (0, 0) but drawn with a 15 mm margin from the page edges.
drawer = AIDrawer(
    page_size=(210, 297),
    unit=UNIT_MM,
    ruler_origin=(15, 15),          # 15 mm left + top margin
    coord_system=COORD_TOP_LEFT,
    layers=layers,
)
drawer.draw()
```

### Reusing the instance across multiple saves

```python
drawer = AIDrawer(page_size=(210, 297), unit=UNIT_MM,
                  coord_system=COORD_TOP_LEFT, layers=layers)
drawer.draw()
drawer.save("output.ai")
drawer.save("output.pdf")   # save again in a different format
drawer.close()
```

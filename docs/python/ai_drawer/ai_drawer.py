import os
import win32com.client


COORD_BOTTOM_LEFT = "bottom-left"   # Illustrator native: origin at bottom-left, Y up
COORD_TOP_LEFT    = "top-left"      # Screen convention:  origin at top-left,    Y down

UNIT_PT = "pt"   # points  — Illustrator native (1 pt = 1/72 in)
UNIT_MM = "mm"   # millimetres
UNIT_IN = "in"   # inches

_PT_PER_UNIT = {
    UNIT_PT: 1.0,
    UNIT_MM: 72.0 / 25.4,
    UNIT_IN: 72.0,
}


class AIDrawer:
    """
    Helper class for drawing layered vector paths in Adobe Illustrator via COM.

    Usage:
        drawer = AIDrawer(
            page_size=(210, 297),       # A4 in mm
            unit=UNIT_MM,
            ruler_origin=(0, 0),
            coord_system=COORD_BOTTOM_LEFT,
            layers=[...]
        )
        drawer.draw()
        drawer.save("output.ai")
        drawer.close()

    Units (unit):
        UNIT_PT  (default) — points, Illustrator's native unit (1 pt = 1/72 in)
        UNIT_MM            — millimetres
        UNIT_IN            — inches

        All caller values are automatically converted to points internally,
        including page_size, ruler_origin, path coordinates, and stroke_width.

    Coordinate systems (coord_system):
        COORD_BOTTOM_LEFT  (default)
            Illustrator's native system.
            Origin at bottom-left of the page, X right, Y up.
            Rectangle/Ellipse "top" = the higher Y value (top edge in Y-up space).

        COORD_TOP_LEFT
            Screen / CSS convention.
            Origin at top-left of the page, X right, Y down.
            Rectangle/Ellipse "top" = distance from the top edge downward.

    Supported path types:
        line        — {"type": "line", "points": [(x1,y1), (x2,y2), ...]}
        rectangle   — {"type": "rectangle", "left": n, "top": n, "width": n, "height": n}
        ellipse     — {"type": "ellipse",   "left": n, "top": n, "width": n, "height": n}

    Layer definition:
        {
            "name":         str,        # layer name in Illustrator
            "color":        (r, g, b),  # stroke color 0-255, default (0, 0, 0)
            "stroke_width": float,      # in the caller's unit, default 1 pt
            "paths":        [...]       # list of path dicts
        }
    """

    def __init__(self, page_size=(612, 792), ruler_origin=(0, 0),
                 unit=UNIT_PT, coord_system=COORD_BOTTOM_LEFT, layers=None):
        if unit not in _PT_PER_UNIT:
            raise ValueError(f"Unknown unit '{unit}'. Use UNIT_PT, UNIT_MM, or UNIT_IN.")
        self.unit         = unit
        self.coord_system = coord_system
        self.layers       = layers or []
        self._doc         = None

        # Convert page_size and ruler_origin to points immediately so all
        # internal arithmetic is always in points.
        self._page_pt   = (self._u(page_size[0]),    self._u(page_size[1]))
        self._origin_pt = (self._u(ruler_origin[0]), self._u(ruler_origin[1]))

    # ------------------------------------------------------------------ #
    #  Unit conversion
    # ------------------------------------------------------------------ #

    def _u(self, value):
        """Convert a scalar from the caller's unit to points."""
        return value * _PT_PER_UNIT[self.unit]

    # ------------------------------------------------------------------ #
    #  Coordinate helpers
    # ------------------------------------------------------------------ #

    def _to_ai(self, x, y):
        """Convert a caller point (in caller units) to Illustrator native coords (pt)."""
        ox, oy = self._origin_pt
        px, py = self._u(x), self._u(y)
        if self.coord_system == COORD_TOP_LEFT:
            return ox + px, self._page_pt[1] - (oy + py)
        else:
            return ox + px, oy + py

    def _to_ai_top(self, left, top):
        """Return (ai_top, ai_left) for Illustrator shape methods (top, left, w, h)."""
        ai_left, ai_top = self._to_ai(left, top)
        return ai_top, ai_left

    # ------------------------------------------------------------------ #
    #  Color
    # ------------------------------------------------------------------ #

    @staticmethod
    def _make_color(r, g, b):
        color = win32com.client.Dispatch("Illustrator.RGBColor")
        color.Red   = r
        color.Green = g
        color.Blue  = b
        return color

    # ------------------------------------------------------------------ #
    #  Shape drawers
    # ------------------------------------------------------------------ #

    def _draw_line(self, layer_obj, path, stroke_color, stroke_width):
        item = layer_obj.PathItems.Add()
        item.Stroked     = True
        item.Filled      = False
        item.StrokeWidth = stroke_width
        item.StrokeColor = stroke_color
        for x, y in path["points"]:
            ai_x, ai_y = self._to_ai(x, y)
            pp = item.PathPoints.Add()
            pp.Anchor         = [ai_x, ai_y]
            pp.LeftDirection  = [ai_x, ai_y]
            pp.RightDirection = [ai_x, ai_y]
        return item

    def _draw_rectangle(self, layer_obj, path, stroke_color, stroke_width):
        ai_top, ai_left = self._to_ai_top(path["left"], path["top"])
        item = layer_obj.PathItems.Rectangle(
            ai_top, ai_left, self._u(path["width"]), self._u(path["height"]))
        item.Stroked     = True
        item.Filled      = False
        item.StrokeWidth = stroke_width
        item.StrokeColor = stroke_color
        return item

    def _draw_ellipse(self, layer_obj, path, stroke_color, stroke_width):
        ai_top, ai_left = self._to_ai_top(path["left"], path["top"])
        item = layer_obj.PathItems.Ellipse(
            ai_top, ai_left, self._u(path["width"]), self._u(path["height"]))
        item.Stroked     = True
        item.Filled      = False
        item.StrokeWidth = stroke_width
        item.StrokeColor = stroke_color
        return item

    # ------------------------------------------------------------------ #
    #  Public API
    # ------------------------------------------------------------------ #

    def draw(self):
        """Open Illustrator, create a document, and draw all layers."""
        ai = win32com.client.Dispatch("Illustrator.Application")

        doc_preset        = win32com.client.Dispatch("Illustrator.DocumentPreset")
        doc_preset.Width  = self._page_pt[0]
        doc_preset.Height = self._page_pt[1]
        self._doc = ai.Documents.AddDocument("", doc_preset)

        drawers = {
            "line":      self._draw_line,
            "rectangle": self._draw_rectangle,
            "ellipse":   self._draw_ellipse,
        }

        for layer_def in self.layers:
            ai_layer      = self._doc.Layers.Add()
            ai_layer.Name = layer_def["name"]

            r, g, b      = layer_def.get("color", (0, 0, 0))
            stroke_color = self._make_color(r, g, b)
            stroke_width = self._u(layer_def.get("stroke_width", 1))

            for path in layer_def.get("paths", []):
                drawer = drawers.get(path["type"])
                if drawer is None:
                    raise ValueError(f"Unsupported path type '{path['type']}' in layer '{layer_def['name']}'.")

                drawer(ai_layer, path, stroke_color, stroke_width)

        return self._doc

    def save(self, filename):
        """Save the document. Format is inferred from the file extension.

        Supported extensions: .ai, .pdf, .eps, .svg
        """
        if self._doc is None:
            raise RuntimeError("No document to save — call draw() first.")

        ext      = os.path.splitext(filename)[1].lower()
        abs_path = os.path.abspath(filename)

        if ext == ".ai":
            options = win32com.client.Dispatch("Illustrator.IllustratorSaveOptions")
            self._doc.SaveAs(abs_path, options)
        elif ext == ".pdf":
            options = win32com.client.Dispatch("Illustrator.PDFSaveOptions")
            self._doc.SaveAs(abs_path, options)
        elif ext == ".eps":
            options = win32com.client.Dispatch("Illustrator.EPSSaveOptions")
            self._doc.SaveAs(abs_path, options)
        elif ext == ".svg":
            options = win32com.client.Dispatch("Illustrator.SVGSaveOptions")
            self._doc.SaveAs(abs_path, options)
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Use .ai, .pdf, .eps, or .svg.")

    def close(self, save=False):
        """Close the document.

        Args:
            save: If True, save before closing (requires a prior save() call).
                  Defaults to False (close without saving).
        """
        if self._doc is None:
            return
        # aiDoNotSaveChanges=2, aiSaveChanges=1
        self._doc.Close(1 if save else 2)
        self._doc = None

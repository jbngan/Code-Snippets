import sys
from ai_drawer import AIDrawer, UNIT_MM, UNIT_IN, COORD_TOP_LEFT

# ---------------------------------------------------------------------------
#  Test data — mm, A4, top-left coords
# ---------------------------------------------------------------------------
LAYERS_MM = [
    {
        "name": "Lines",
        "color": (255, 0, 0),
        "stroke_width": 0.5,        # 0.5 mm
        "paths": [
            {"type": "line", "points": [(10,  10), (100,  10)]},
            {"type": "line", "points": [(10,  20), (100,  60)]},
            {"type": "line", "points": [(20,  80), (180, 150)]},
        ],
    },
    {
        "name": "Rectangles",
        "color": (0, 128, 0),
        "stroke_width": 0.5,
        "paths": [
            {"type": "rectangle", "left": 10, "top":  10, "width": 60,  "height": 30},
            {"type": "rectangle", "left": 90, "top":  60, "width": 50,  "height": 25},
            {"type": "rectangle", "left": 30, "top": 110, "width": 100, "height": 20},
        ],
    },
    {
        "name": "Ellipses",
        "color": (0, 0, 255),
        "stroke_width": 0.5,
        "paths": [
            {"type": "ellipse", "left":  10, "top":  10, "width": 50, "height": 30},
            {"type": "ellipse", "left":  80, "top":  60, "width": 35, "height": 35},
            {"type": "ellipse", "left": 130, "top": 100, "width": 60, "height": 25},
        ],
    },
]

# ---------------------------------------------------------------------------
#  Test data — inches, Letter, top-left coords
# ---------------------------------------------------------------------------
LAYERS_IN = [
    {
        "name": "Lines",
        "color": (255, 0, 0),
        "stroke_width": 0.01,       # 0.01 in ≈ 0.72 pt
        "paths": [
            {"type": "line", "points": [(0.5, 0.5), (4.0, 0.5)]},
            {"type": "line", "points": [(0.5, 1.0), (4.0, 3.0)]},
        ],
    },
    {
        "name": "Rectangles",
        "color": (0, 128, 0),
        "stroke_width": 0.01,
        "paths": [
            {"type": "rectangle", "left": 0.5, "top": 0.5, "width": 2.0, "height": 1.0},
            {"type": "rectangle", "left": 3.0, "top": 2.5, "width": 1.5, "height": 0.8},
        ],
    },
]

# ---------------------------------------------------------------------------
#  Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # mm, A4, top-left coords (good for print work)
    drawer = AIDrawer(page_size=(210, 297), unit=UNIT_MM,
                      coord_system=COORD_TOP_LEFT, layers=LAYERS_MM)

    # inches, Letter, top-left coords
    # drawer = AIDrawer(page_size=(8.5, 11), unit=UNIT_IN,
    #                   coord_system=COORD_TOP_LEFT, layers=LAYERS_IN)

    drawer.draw()
    # drawer.save("test_output.ai")   # also supports .pdf, .eps, .svg
    # drawer.close()                  # close without saving
    # drawer.close(save=True)         # close and keep (requires a prior save() call)

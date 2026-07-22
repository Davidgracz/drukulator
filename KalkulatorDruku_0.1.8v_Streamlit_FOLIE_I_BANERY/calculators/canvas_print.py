"""
Plik zgodności dla projektów, które importują kalkulator jako
calculators.canvas_print zamiast calculators.canvas.
"""

from calculators.canvas import (
    CUSTOM_MODE,
    STANDARD_MODE,
    calculate_custom_canvas,
    calculate_standard_canvas,
    find_billing_format,
    get_canvas_data,
    parse_canvas_format,
    render,
)

__all__ = [
    "CUSTOM_MODE",
    "STANDARD_MODE",
    "calculate_custom_canvas",
    "calculate_standard_canvas",
    "find_billing_format",
    "get_canvas_data",
    "parse_canvas_format",
    "render",
]

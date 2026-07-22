from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Optional, Tuple

import streamlit as st
from PIL import Image, ImageOps

from calculators.loader import load_prices
from calculators.shared import add_to_cart_button
from core.formatting import money


STANDARD_MODE = "Gotowy format z cennika"
CUSTOM_MODE = "Własny wymiar"


def parse_canvas_format(format_name: str) -> Tuple[float, float]:
    """
    Zamienia nazwę formatu, np. 30x40, na dwie liczby.
    """
    match = re.fullmatch(
        r"\s*(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*",
        str(format_name),
    )

    if not match:
        raise ValueError(
            "Nieprawidłowa nazwa formatu w data/prices.json: "
            f"{format_name!r}."
        )

    width = float(match.group(1).replace(",", "."))
    height = float(match.group(2).replace(",", "."))
    return width, height


def _normalise_dimension(value: float) -> float:
    return round(float(value), 1)


def _format_dimension(value: float) -> str:
    value = float(value)
    if value.is_integer():
        return str(int(value))
    return f"{value:.1f}".replace(".", ",")


def get_canvas_data(
    prices: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if prices is None:
        prices = load_prices()

    if "obrazy_na_plotnie" not in prices:
        raise ValueError(
            "W data/prices.json brakuje sekcji „obrazy_na_plotnie”."
        )

    canvas_data = prices["obrazy_na_plotnie"]

    if "formaty" not in canvas_data or not canvas_data["formaty"]:
        raise ValueError(
            "W sekcji „obrazy_na_plotnie” brakuje cennika „formaty”."
        )

    return canvas_data


def validate_custom_size(
    width_cm: float,
    height_cm: float,
    canvas_data: Mapping[str, Any],
) -> Tuple[float, float]:
    width_cm = _normalise_dimension(width_cm)
    height_cm = _normalise_dimension(height_cm)

    if width_cm <= 0 or height_cm <= 0:
        raise ValueError("Szerokość i wysokość muszą być większe od zera.")

    minimum_side = float(canvas_data.get("minimalny_bok_cm", 30))
    maximum_side = float(canvas_data.get("maksymalny_bok_cm", 150))

    if width_cm < minimum_side or height_cm < minimum_side:
        raise ValueError(
            "Każdy bok obrazu musi mieć co najmniej "
            f"{_format_dimension(minimum_side)} cm."
        )

    if width_cm > maximum_side or height_cm > maximum_side:
        raise ValueError(
            "Każdy bok obrazu może mieć maksymalnie "
            f"{_format_dimension(maximum_side)} cm."
        )

    return width_cm, height_cm


def get_billing_candidates(
    format_prices: Mapping[str, Any],
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []

    for format_name, raw_price in format_prices.items():
        first_side, second_side = parse_canvas_format(format_name)
        price = float(raw_price)

        orientations = {
            (first_side, second_side),
            (second_side, first_side),
        }

        for width_cm, height_cm in orientations:
            candidates.append(
                {
                    "format_name": str(format_name),
                    "width_cm": float(width_cm),
                    "height_cm": float(height_cm),
                    "area_cm2": float(width_cm) * float(height_cm),
                    "price": price,
                }
            )

    return candidates


def find_billing_format(
    width_cm: float,
    height_cm: float,
    prices: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Własny rozmiar jest rozliczany według najmniejszego formatu
    z cennika, który mieści podaną szerokość i wysokość.
    """
    canvas_data = get_canvas_data(prices)
    width_cm, height_cm = validate_custom_size(
        width_cm,
        height_cm,
        canvas_data,
    )

    candidates = get_billing_candidates(canvas_data["formaty"])

    matching = [
        item
        for item in candidates
        if item["width_cm"] >= width_cm
        and item["height_cm"] >= height_cm
    ]

    if not matching:
        raise ValueError(
            "Nie znaleziono w cenniku formatu, który mieści podany wymiar."
        )

    matching.sort(
        key=lambda item: (
            item["area_cm2"],
            (item["width_cm"] - width_cm)
            + (item["height_cm"] - height_cm),
            max(
                item["width_cm"] - width_cm,
                item["height_cm"] - height_cm,
            ),
            item["price"],
        )
    )

    selected = dict(matching[0])
    selected["requested_width_cm"] = width_cm
    selected["requested_height_cm"] = height_cm
    selected["billing_method"] = "Najbliższy większy format z cennika"
    return selected


def calculate_custom_canvas(
    width_cm: float,
    height_cm: float,
    quantity: int,
    prices: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if int(quantity) <= 0:
        raise ValueError("Liczba obrazów musi być większa od zera.")

    quantity = int(quantity)
    billing = find_billing_format(width_cm, height_cm, prices)
    unit_price = float(billing["price"])
    total_price = unit_price * quantity

    return {
        "mode": CUSTOM_MODE,
        "width_cm": billing["requested_width_cm"],
        "height_cm": billing["requested_height_cm"],
        "billing_format": billing["format_name"],
        "billing_width_cm": billing["width_cm"],
        "billing_height_cm": billing["height_cm"],
        "billing_method": billing["billing_method"],
        "unit_price": round(unit_price, 2),
        "quantity": quantity,
        "price": round(total_price, 2),
    }


def calculate_standard_canvas(
    format_name: str,
    quantity: int,
    prices: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if int(quantity) <= 0:
        raise ValueError("Liczba obrazów musi być większa od zera.")

    canvas_data = get_canvas_data(prices)
    format_prices = canvas_data["formaty"]

    if format_name not in format_prices:
        raise ValueError("Nie znaleziono wybranego formatu w cenniku.")

    width_cm, height_cm = parse_canvas_format(format_name)
    quantity = int(quantity)
    unit_price = float(format_prices[format_name])

    return {
        "mode": STANDARD_MODE,
        "format_name": format_name,
        "width_cm": width_cm,
        "height_cm": height_cm,
        "unit_price": round(unit_price, 2),
        "quantity": quantity,
        "price": round(unit_price * quantity, 2),
    }


def _show_uploaded_image() -> Optional[Tuple[int, int]]:
    uploaded_file = st.file_uploader(
        "Zdjęcie do podglądu (opcjonalnie)",
        type=["jpg", "jpeg", "png", "tif", "tiff", "webp"],
        key="canvas_uploaded_image",
        help=(
            "Zdjęcie nie jest potrzebne do samego obliczenia ceny. "
            "Służy do podglądu i sprawdzenia proporcji."
        ),
    )

    if uploaded_file is None:
        return None

    try:
        with Image.open(uploaded_file) as source_image:
            image = ImageOps.exif_transpose(source_image)
            width_px, height_px = image.size
            preview = image.convert("RGB")

        preview_column, info_column = st.columns([2, 1])

        with preview_column:
            st.image(
                preview,
                caption=uploaded_file.name,
                use_column_width=True,
            )

        with info_column:
            orientation = "pozioma"
            if height_px > width_px:
                orientation = "pionowa"
            elif height_px == width_px:
                orientation = "kwadratowa"

            st.metric("Wymiary pliku", f"{width_px} × {height_px} px")
            st.caption(f"Orientacja: {orientation}")

        return width_px, height_px

    except (OSError, ValueError) as exc:
        st.warning(f"Nie udało się odczytać zdjęcia: {exc}")
        return None


def _render_standard_mode(
    canvas_data: Mapping[str, Any],
    quantity: int,
    prices: Dict[str, Any],
) -> None:
    format_prices = canvas_data["formaty"]
    format_names = list(format_prices.keys())

    selected_format = st.selectbox(
        "Format obrazu",
        format_names,
        format_func=lambda name: (
            f"{name.replace('x', ' × ')} cm — "
            f"{money(float(format_prices[name]))}"
        ),
        key="canvas_standard_format",
    )

    result = calculate_standard_canvas(
        selected_format,
        quantity,
        prices=prices,
    )

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric(
        "Wymiar",
        (
            f"{_format_dimension(result['width_cm'])} × "
            f"{_format_dimension(result['height_cm'])} cm"
        ),
    )
    metric_2.metric("Cena za sztukę", money(result["unit_price"]))
    metric_3.metric("Cena razem", money(result["price"]))

    details = (
        f"Format: {_format_dimension(result['width_cm'])} × "
        f"{_format_dimension(result['height_cm'])} cm; "
        f"ilość: {result['quantity']} szt.; "
        f"cena jednostkowa: {money(result['unit_price'])}"
    )

    add_to_cart_button(
        key=(
            "add_canvas_standard_"
            f"{selected_format}_{result['quantity']}"
        ),
        name="Obraz na płótnie",
        details=details,
        price=result["price"],
    )


def _render_custom_mode(
    canvas_data: Mapping[str, Any],
    quantity: int,
    prices: Dict[str, Any],
    image_size: Optional[Tuple[int, int]],
) -> None:
    minimum_side = float(canvas_data.get("minimalny_bok_cm", 30))
    maximum_side = float(canvas_data.get("maksymalny_bok_cm", 150))

    st.caption(
        "Wpisz gotowy wymiar obrazu w centymetrach. "
        "Cena zostanie pokazana automatycznie."
    )

    width_column, height_column = st.columns(2)

    with width_column:
        width_cm = float(
            st.number_input(
                "Szerokość obrazu [cm]",
                min_value=minimum_side,
                max_value=maximum_side,
                value=minimum_side,
                step=1.0,
                format="%.1f",
                key="canvas_custom_width",
            )
        )

    with height_column:
        height_cm = float(
            st.number_input(
                "Wysokość obrazu [cm]",
                min_value=minimum_side,
                max_value=maximum_side,
                value=minimum_side,
                step=1.0,
                format="%.1f",
                key="canvas_custom_height",
            )
        )

    if image_size:
        image_width_px, image_height_px = image_size
        image_ratio = image_width_px / image_height_px
        requested_ratio = width_cm / height_cm
        ratio_difference = (
            abs(requested_ratio - image_ratio)
            / image_ratio
            * 100
        )

        if ratio_difference < 0.5:
            st.success("Podany wymiar zachowuje proporcje wczytanego zdjęcia.")
        else:
            st.info(
                "Podany wymiar różni się od proporcji zdjęcia o "
                f"{ratio_difference:.1f}%. Może być potrzebne kadrowanie."
            )

    try:
        result = calculate_custom_canvas(
            width_cm,
            height_cm,
            quantity,
            prices=prices,
        )
    except ValueError as exc:
        st.warning(str(exc))
        add_to_cart_button(
            key="add_canvas_custom_disabled",
            name="Obraz na płótnie",
            details="Nieprawidłowy wymiar.",
            price=0.0,
            disabled=True,
        )
        return

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric(
        "Twój wymiar",
        (
            f"{_format_dimension(result['width_cm'])} × "
            f"{_format_dimension(result['height_cm'])} cm"
        ),
    )
    metric_2.metric("Cena za sztukę", money(result["unit_price"]))
    metric_3.metric("Cena razem", money(result["price"]))

    st.info(
        "Format rozliczeniowy: "
        f"{_format_dimension(result['billing_width_cm'])} × "
        f"{_format_dimension(result['billing_height_cm'])} cm "
        f"({result['billing_format']}). "
        f"{result['billing_method']}."
    )

    details = (
        f"Własny wymiar: {_format_dimension(result['width_cm'])} × "
        f"{_format_dimension(result['height_cm'])} cm; "
        f"format rozliczeniowy: "
        f"{_format_dimension(result['billing_width_cm'])} × "
        f"{_format_dimension(result['billing_height_cm'])} cm; "
        f"ilość: {result['quantity']} szt.; "
        f"cena jednostkowa: {money(result['unit_price'])}"
    )

    add_to_cart_button(
        key=(
            "add_canvas_custom_"
            f"{result['width_cm']}_{result['height_cm']}_"
            f"{result['quantity']}_{result['billing_format']}"
        ),
        name="Obraz na płótnie — własny wymiar",
        details=details,
        price=result["price"],
    )


def render(prices: Optional[Dict[str, Any]] = None) -> None:
    """
    Rysuje kalkulator obrazów na płótnie w interfejsie Streamlit.
    """
    if prices is None:
        prices = load_prices()

    st.header("Obrazy na płótnie")

    canvas_data = get_canvas_data(prices)

    material = canvas_data.get("material")
    if material:
        st.caption(material)

    image_size = _show_uploaded_image()

    mode_column, quantity_column = st.columns([3, 1])

    with mode_column:
        mode = st.radio(
            "Sposób wyboru rozmiaru",
            [STANDARD_MODE, CUSTOM_MODE],
            horizontal=True,
            key="canvas_size_mode",
        )

    with quantity_column:
        quantity = int(
            st.number_input(
                "Liczba obrazów",
                min_value=1,
                value=1,
                step=1,
                key="canvas_quantity",
            )
        )

    st.divider()

    if mode == CUSTOM_MODE:
        _render_custom_mode(
            canvas_data,
            quantity,
            prices,
            image_size,
        )
    else:
        _render_standard_mode(
            canvas_data,
            quantity,
            prices,
        )

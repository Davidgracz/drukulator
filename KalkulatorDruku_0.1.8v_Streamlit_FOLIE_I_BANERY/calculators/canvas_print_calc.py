import math
import re

from calculators.loader import load_prices


def parse_canvas_format(format_key):
    """
    Zamienia klucz np. 30x60 na dwie liczby całkowite.
    """

    match = re.fullmatch(
        r"\s*(\d+)\s*[x×]\s*(\d+)\s*",
        str(format_key)
    )

    if not match:
        raise ValueError(
            f"Nieprawidłowy format obrazu: {format_key}."
        )

    return (
        int(match.group(1)),
        int(match.group(2))
    )


def get_canvas_data():
    """
    Wczytuje cennik obrazów na płótnie.
    """

    prices = load_prices()

    return prices[
        "obrazy_na_plotnie"
    ]


def get_canvas_suggestions(
    image_width_px,
    image_height_px,
    minimum_results=8
):
    """
    Zwraca formaty najlepiej dopasowane do proporcji pliku.

    Orientacja obrazu jest zachowana:
    - zdjęcie poziome otrzymuje formaty poziome,
    - zdjęcie pionowe otrzymuje formaty pionowe.
    """

    if image_width_px <= 0 or image_height_px <= 0:
        raise ValueError(
            "Wymiary obrazu muszą być większe od zera."
        )

    canvas_data = get_canvas_data()
    format_prices = canvas_data["formaty"]

    image_ratio = (
        float(image_width_px)
        / float(image_height_px)
    )

    is_landscape = image_width_px > image_height_px
    is_portrait = image_height_px > image_width_px

    candidates = []

    for format_key, price in format_prices.items():

        first_side, second_side = parse_canvas_format(
            format_key
        )

        smaller_side = min(
            first_side,
            second_side
        )

        larger_side = max(
            first_side,
            second_side
        )

        if is_landscape:
            display_width_cm = larger_side
            display_height_cm = smaller_side

        elif is_portrait:
            display_width_cm = smaller_side
            display_height_cm = larger_side

        else:
            display_width_cm = first_side
            display_height_cm = second_side

        candidate_ratio = (
            display_width_cm
            / display_height_cm
        )

        ratio_error_percent = (
            abs(candidate_ratio - image_ratio)
            / image_ratio
            * 100
        )

        candidates.append(
            {
                "format_key": format_key,
                "display_width_cm": display_width_cm,
                "display_height_cm": display_height_cm,
                "price": float(price),
                "image_ratio": image_ratio,
                "format_ratio": candidate_ratio,
                "ratio_error_percent": (
                    ratio_error_percent
                ),
                "area_cm2": (
                    display_width_cm
                    * display_height_cm
                )
            }
        )

    candidates.sort(
        key=lambda item: (
            round(
                item["ratio_error_percent"],
                10
            ),
            item["area_cm2"]
        )
    )

    if not candidates:
        return []

    best_error = candidates[0][
        "ratio_error_percent"
    ]

    best_matches = [
        candidate
        for candidate in candidates
        if math.isclose(
            candidate["ratio_error_percent"],
            best_error,
            rel_tol=1e-9,
            abs_tol=1e-9
        )
    ]

    # Dla proporcji takich jak 1:2 pokazujemy wszystkie
    # idealnie pasujące formaty: 30x60, 40x80 itd.
    if len(best_matches) >= 3:
        return best_matches

    result_count = max(
        int(minimum_results),
        len(best_matches)
    )

    return candidates[
        :result_count
    ]


def calculate_proportional_canvas_size(
    image_width_px,
    image_height_px,
    known_side,
    known_value_cm
):
    """
    Oblicza drugi bok obrazu z zachowaniem proporcji pliku.

    known_side:
        "Szerokość" albo "Wysokość"
    """

    if image_width_px <= 0 or image_height_px <= 0:
        raise ValueError(
            "Wymiary obrazu muszą być większe od zera."
        )

    if known_value_cm <= 0:
        raise ValueError(
            "Podany wymiar musi być większy od zera."
        )

    if known_side not in (
        "Szerokość",
        "Wysokość"
    ):
        raise ValueError(
            "Wybierz, czy podajesz szerokość czy wysokość."
        )

    image_ratio = (
        float(image_width_px)
        / float(image_height_px)
    )

    if known_side == "Szerokość":

        width_cm = float(
            known_value_cm
        )

        height_cm = (
            width_cm
            / image_ratio
        )

    else:

        height_cm = float(
            known_value_cm
        )

        width_cm = (
            height_cm
            * image_ratio
        )

    width_cm = round(
        width_cm,
        1
    )

    height_cm = round(
        height_cm,
        1
    )

    canvas_data = get_canvas_data()

    minimum_side_cm = float(
        canvas_data.get(
            "minimalny_bok_cm",
            30
        )
    )

    maximum_side_cm = float(
        canvas_data.get(
            "maksymalny_bok_cm",
            150
        )
    )

    if max(width_cm, height_cm) > maximum_side_cm:
        raise ValueError(
            "Po zachowaniu proporcji najdłuższy bok "
            f"ma {max(width_cm, height_cm):.1f} cm. "
            f"Maksymalny bok to {maximum_side_cm:.0f} cm."
        )

    if min(width_cm, height_cm) < minimum_side_cm:
        raise ValueError(
            "Po zachowaniu proporcji krótszy bok "
            f"ma {min(width_cm, height_cm):.1f} cm. "
            f"Minimalny bok z cennika to "
            f"{minimum_side_cm:.0f} cm."
        )

    return {
        "width_cm": width_cm,
        "height_cm": height_cm,
        "known_side": known_side,
        "known_value_cm": float(
            known_value_cm
        ),
        "minimum_side_cm": minimum_side_cm,
        "maximum_side_cm": maximum_side_cm
    }


def find_canvas_billing_format(
    width_cm,
    height_cm
):
    """
    Dobiera format rozliczeniowy z cennika.

    Najpierw szuka najmniejszego formatu, który jest
    co najmniej tak duży w obu kierunkach. Gdy taki format
    nie istnieje, wybiera format najbardziej zbliżony
    wymiarami i powierzchnią.
    """

    if width_cm <= 0 or height_cm <= 0:
        raise ValueError(
            "Wymiary obrazu muszą być większe od zera."
        )

    canvas_data = get_canvas_data()
    format_prices = canvas_data["formaty"]

    requested_area = (
        float(width_cm)
        * float(height_cm)
    )

    candidates = []

    for format_key, price in format_prices.items():

        first_side, second_side = parse_canvas_format(
            format_key
        )

        orientations = {
            (
                float(first_side),
                float(second_side)
            ),
            (
                float(second_side),
                float(first_side)
            )
        }

        for display_width_cm, display_height_cm in orientations:

            area_cm2 = (
                display_width_cm
                * display_height_cm
            )

            contains_requested_size = (
                display_width_cm >= width_cm
                and display_height_cm >= height_cm
            )

            dimension_difference = (
                abs(display_width_cm - width_cm)
                + abs(display_height_cm - height_cm)
            )

            candidates.append(
                {
                    "format_key": format_key,
                    "display_width_cm": (
                        display_width_cm
                    ),
                    "display_height_cm": (
                        display_height_cm
                    ),
                    "price": float(price),
                    "area_cm2": area_cm2,
                    "area_difference": abs(
                        area_cm2 - requested_area
                    ),
                    "dimension_difference": (
                        dimension_difference
                    ),
                    "contains_requested_size": (
                        contains_requested_size
                    )
                }
            )

    containing_candidates = [
        candidate
        for candidate in candidates
        if candidate[
            "contains_requested_size"
        ]
    ]

    if containing_candidates:

        containing_candidates.sort(
            key=lambda item: (
                item["area_cm2"],
                item["dimension_difference"],
                item["price"]
            )
        )

        selected = containing_candidates[0]
        selected["billing_method"] = (
            "Najbliższy większy format z cennika"
        )

        return selected

    candidates.sort(
        key=lambda item: (
            item["dimension_difference"],
            item["area_difference"],
            item["price"]
        )
    )

    selected = candidates[0]
    selected["billing_method"] = (
        "Najbliższy dostępny format z cennika"
    )

    return selected


def calculate_canvas_print(
    format_key,
    quantity
):
    """
    Oblicza cenę standardowego formatu obrazu na płótnie.
    """

    if quantity <= 0:
        raise ValueError(
            "Ilość musi być większa od zera."
        )

    canvas_data = get_canvas_data()
    format_prices = canvas_data["formaty"]

    if format_key not in format_prices:
        raise ValueError(
            "Nie znaleziono wybranego formatu "
            "w cenniku obrazów na płótnie."
        )

    width_cm, height_cm = parse_canvas_format(
        format_key
    )

    unit_price = float(
        format_prices[
            format_key
        ]
    )

    total_price = (
        unit_price
        * quantity
    )

    return {
        "price": round(
            total_price,
            2
        ),
        "unit_price": round(
            unit_price,
            2
        ),
        "quantity": quantity,
        "format_key": format_key,
        "width_cm": width_cm,
        "height_cm": height_cm,
        "max_side_cm": int(
            canvas_data.get(
                "maksymalny_bok_cm",
                150
            )
        )
    }


def calculate_custom_canvas_print(
    width_cm,
    height_cm,
    quantity
):
    """
    Oblicza cenę własnego rozmiaru obrazu.

    Cena pochodzi z najbliższego większego formatu
    rozliczeniowego dostępnego w cenniku.
    """

    if quantity <= 0:
        raise ValueError(
            "Ilość musi być większa od zera."
        )

    billing_format = find_canvas_billing_format(
        width_cm=width_cm,
        height_cm=height_cm
    )

    unit_price = float(
        billing_format["price"]
    )

    total_price = (
        unit_price
        * quantity
    )

    return {
        "price": round(
            total_price,
            2
        ),
        "unit_price": round(
            unit_price,
            2
        ),
        "quantity": quantity,

        "custom_width_cm": round(
            float(width_cm),
            1
        ),
        "custom_height_cm": round(
            float(height_cm),
            1
        ),

        "billing_format_key": (
            billing_format[
                "format_key"
            ]
        ),
        "billing_width_cm": (
            billing_format[
                "display_width_cm"
            ]
        ),
        "billing_height_cm": (
            billing_format[
                "display_height_cm"
            ]
        ),
        "billing_method": (
            billing_format[
                "billing_method"
            ]
        )
    }

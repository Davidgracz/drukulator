import math

from calculators.loader import load_prices


# Do szerokości i wysokości naklejki dodajemy po 5 mm.
MARGIN_MM = 3.0

# Maksymalna szerokość druku i szerokość folii.
MAX_PRINT_WIDTH_MM = 1000.0
ROLL_WIDTH_MM = 1000.0

# Długość rozliczeniową zaokrąglamy w górę do 0,1 mb.
LENGTH_ROUNDING_STEP_M = 0.1


def round_up_to_step(value, step):
    """
    Zaokrągla wartość zawsze w górę do podanego kroku.

    Przykłady:
    1.21 -> 1.3
    1.30 -> 1.3
    1.31 -> 1.4
    """

    return (
        math.ceil(
            (value / step) - 1e-9
        )
        * step
    )


def calculate_stickers(
    product_type,
    quantity,
    width=None,
    height=None
):
    if quantity <= 0:
        raise ValueError(
            "Ilość musi być większa od zera."
        )

    prices = load_prices()
    stickers_data = prices["naklejki"]

    if product_type in stickers_data["powierzchniowe"]:

        if width is None or height is None:
            raise ValueError(
                "Podaj szerokość i wysokość."
            )

        if width <= 0 or height <= 0:
            raise ValueError(
                "Wymiary muszą być większe od zera."
            )

        product_data = stickers_data[
            "powierzchniowe"
        ][product_type]

        # Przy folii szerokiej na 1000 mm:
        # 100 zł/m² = 100 zł/mb.
        price_per_linear_meter = float(
            product_data["cena_m2"]
        )

        minimum_m2 = float(
            product_data["minimum_m2"]
        )

        # Użytkownik wpisuje wymiary w centymetrach.
        actual_width_mm = width * 10
        actual_height_mm = height * 10

        # Dodajemy 5 mm do całkowitej szerokości
        # i 5 mm do całkowitej wysokości.
        production_width_mm = (
            actual_width_mm
            + MARGIN_MM
        )

        production_height_mm = (
            actual_height_mm
            + MARGIN_MM
        )

        if production_width_mm > MAX_PRINT_WIDTH_MM:
            raise ValueError(
                "Naklejka po dodaniu 5 mm przekracza "
                "maksymalną szerokość folii 1000 mm."
            )

        # Maksymalna całkowita liczba naklejek w rzędzie.
        stickers_per_row = math.floor(
            MAX_PRINT_WIDTH_MM
            / production_width_mm
        )

        if stickers_per_row < 1:
            raise ValueError(
                "Na szerokości 1000 mm nie mieści się "
                "ani jedna naklejka."
            )

        # Liczba potrzebnych rzędów.
        rows = math.ceil(
            quantity
            / stickers_per_row
        )

        # Wszystkie miejsca w ostatnim rzędzie
        # także zostają zapełnione naklejkami.
        total_stickers = (
            stickers_per_row
            * rows
        )

        extra_stickers = (
            total_stickers
            - quantity
        )

        # Faktyczna szerokość zajęta przez układ.
        layout_width_mm = (
            stickers_per_row
            * production_width_mm
        )

        # Potrzebna długość folii.
        base_length_mm = (
            rows
            * production_height_mm
        )

        base_length_m = (
            base_length_mm
            / 1000
        )

        # Powierzchnia zamówionych naklejek bez marginesów.
        actual_area_m2 = (
            actual_width_mm
            * actual_height_mm
            * quantity
            / 1_000_000
        )

        # Powierzchnia wszystkich wykonanych naklejek
        # razem z marginesem i dodatkowymi sztukami.
        production_area_m2 = (
            production_width_mm
            * production_height_mm
            * total_stickers
            / 1_000_000
        )

        roll_width_m = (
            ROLL_WIDTH_MM
            / 1000
        )

        # Przy rolce 1000 mm powierzchnia zużytej folii
        # jest równa liczbie metrów bieżących.
        base_roll_area_m2 = (
            roll_width_m
            * base_length_m
        )

        # Minimalna powierzchnia z cennika.
        # Przy szerokości 1 m:
        # 1 m² = 1 mb.
        minimum_length_m = (
            minimum_m2
            / roll_width_m
        )

        required_length_m = max(
            base_length_m,
            minimum_length_m
        )

        # Zaokrąglenie zawsze w górę do 0,1 mb.
        billed_length_m = round_up_to_step(
            required_length_m,
            LENGTH_ROUNDING_STEP_M
        )

        billed_area_m2 = (
            roll_width_m
            * billed_length_m
        )

        total_price = (
            billed_length_m
            * price_per_linear_meter
        )

        return {
            "price": round(total_price, 2),

            "price_per_linear_meter": (
                price_per_linear_meter
            ),

            "area_m2": actual_area_m2,
            "production_area_m2": production_area_m2,
            "base_roll_area_m2": base_roll_area_m2,
            "billed_area_m2": billed_area_m2,

            "base_length_m": base_length_m,
            "required_length_m": required_length_m,
            "billed_length_m": billed_length_m,
            "minimum_length_m": minimum_length_m,

            "actual_width_mm": actual_width_mm,
            "actual_height_mm": actual_height_mm,

            "production_width_mm": production_width_mm,
            "production_height_mm": production_height_mm,

            "stickers_per_row": stickers_per_row,
            "rows": rows,
            "total_stickers": total_stickers,
            "extra_stickers": extra_stickers,

            "layout_width_mm": layout_width_mm,
            "roll_width_mm": ROLL_WIDTH_MM,
            "max_print_width_mm": MAX_PRINT_WIDTH_MM
        }

    if product_type in stickers_data["taxi"]:

        unit_price = float(
            stickers_data[
                "taxi"
            ][
                product_type
            ][
                "cena_sztuki"
            ]
        )

        total_price = (
            unit_price
            * quantity
        )

        return {
            "price": round(total_price, 2),

            "price_per_linear_meter": None,

            "area_m2": None,
            "production_area_m2": None,
            "base_roll_area_m2": None,
            "billed_area_m2": None,

            "base_length_m": None,
            "required_length_m": None,
            "billed_length_m": None,
            "minimum_length_m": None,

            "actual_width_mm": None,
            "actual_height_mm": None,
            "production_width_mm": None,
            "production_height_mm": None,

            "stickers_per_row": None,
            "rows": None,
            "total_stickers": None,
            "extra_stickers": None,

            "layout_width_mm": None,
            "roll_width_mm": None,
            "max_print_width_mm": None
        }

    raise ValueError(
        "Nieobsługiwany rodzaj produktu."
    )
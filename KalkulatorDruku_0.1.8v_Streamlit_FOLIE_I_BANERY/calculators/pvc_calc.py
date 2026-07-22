from calculators.loader import load_prices


def calculate_pvc(
    width: float,
    height: float,
    quantity: int,
    product_type: str
) -> float:

    if width <= 0:
        raise ValueError(
            "Szerokość musi być większa od zera."
        )

    if height <= 0:
        raise ValueError(
            "Wysokość musi być większa od zera."
        )

    if quantity <= 0:
        raise ValueError(
            "Ilość musi być większa od zera."
        )

    prices = load_prices()

    product_data = prices[
        "pvc"
    ][
        product_type
    ]

    price_m2 = float(
        product_data["cena_m2"]
    )

    minimum_order = float(
        product_data["minimum_zamowienia"]
    )

    width_m = width / 100
    height_m = height / 100

    area_one_piece = width_m * height_m
    total_area = area_one_piece * quantity

    calculated_price = total_area * price_m2

    final_price = max(
        calculated_price,
        minimum_order
    )

    return round(final_price, 2)
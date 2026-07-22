from calculators.loader import load_prices


def calculate_rollup(
    product_type: str,
    size: str,
    quantity: int
) -> float:

    if quantity <= 0:
        raise ValueError(
            "Ilość musi być większa od zera."
        )

    prices = load_prices()

    unit_price = prices["rollup"][
        product_type
    ][
        size
    ]

    total_price = float(unit_price) * quantity

    return round(total_price, 2)
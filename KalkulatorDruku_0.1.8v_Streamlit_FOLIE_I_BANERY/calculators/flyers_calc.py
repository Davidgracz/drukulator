from calculators.loader import load_prices


def calculate_flyers(
    print_type: str,
    variant: str,
    format_name: str,
    quantity: int
) -> float:

    if quantity <= 0:
        raise ValueError(
            "Nakład musi być większy od zera."
        )

    prices = load_prices()

    price = prices["ulotki"][
        print_type
    ][
        variant
    ][
        format_name
    ][
        str(quantity)
    ]

    return round(float(price), 2)
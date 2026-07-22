from calculators.loader import load_prices


def calculate_posters(
    print_type: str,
    format_name: str,
    quantity: int
) -> float:

    if quantity <= 0:
        raise ValueError(
            "Ilość musi być większa od zera."
        )

    prices = load_prices()

    poster_prices = prices["plakaty"][print_type]

    if print_type == "Wielkoformatowy":

        unit_price = poster_prices[format_name]

        total_price = float(unit_price) * quantity

    else:

        total_price = poster_prices[
            format_name
        ][
            str(quantity)
        ]

    return round(float(total_price), 2)
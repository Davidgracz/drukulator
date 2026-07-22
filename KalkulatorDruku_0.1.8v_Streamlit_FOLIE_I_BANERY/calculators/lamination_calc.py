from calculators.loader import load_prices


def calculate_lamination(
    format_name,
    quantity
):
    """
    Oblicza cenę laminowania dokumentów
    folią 80 mikronów.
    """

    if quantity <= 0:
        raise ValueError(
            "Ilość musi być większa od zera."
        )

    prices = load_prices()

    lamination_data = prices[
        "laminowanie"
    ]

    format_prices = lamination_data[
        "formaty"
    ]

    if format_name not in format_prices:
        raise ValueError(
            "Nie znaleziono wybranego formatu laminowania."
        )

    unit_price = float(
        format_prices[
            format_name
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

        "format_name": format_name,
        "quantity": quantity,

        "unit_price": round(
            unit_price,
            2
        ),

        "foil_microns": int(
            lamination_data.get(
                "folia_mikrony",
                80
            )
        )
    }

from calculators.loader import load_prices


NO_PRINT = "Brak"


def get_apparel_discount(
    quantity,
    discounts=None
):
    """
    Zwraca rabat zależny od liczby sztuk.

    1-9 sztuk: 0%
    10-20 sztuk: 10%
    21 sztuk i więcej: 20%
    """

    if quantity <= 0:
        raise ValueError(
            "Ilość musi być większa od zera."
        )

    if discounts is None:
        discounts = {
            "od_10_sztuk": 10,
            "powyzej_20_sztuk": 20
        }

    if quantity > 20:
        return float(
            discounts.get(
                "powyzej_20_sztuk",
                20
            )
        )

    if quantity >= 10:
        return float(
            discounts.get(
                "od_10_sztuk",
                10
            )
        )

    return 0.0


def get_print_only_prices(prices):
    """
    Pobiera cennik samego nadruku.
    """

    return prices[
        "odziez_z_nadrukiem"
    ][
        "produkty"
    ][
        "Sam nadruk"
    ][
        "Nadruk na odzieży klienta"
    ][
        "ceny"
    ]


def find_print_only_size(
    selected_size,
    print_only_prices
):
    """
    Dopasowuje nazwę rozmiaru nadruku produktu
    do cennika samego nadruku.

    Obsługuje między innymi:
    - Do 10x15 cm
    - Do 20x30 cm
    - Do 35x40 cm
    - Nadruk 20x30 cm
    - Nadruk standardowy
    """

    if selected_size in print_only_prices:
        return selected_size

    normalized_size = (
        selected_size
        .lower()
        .replace(" ", "")
        .replace("×", "x")
    )

    dimensions = [
        "10x15",
        "20x30",
        "35x40"
    ]

    for dimension in dimensions:

        if dimension in normalized_size:

            for print_size in print_only_prices:

                normalized_print_size = (
                    print_size
                    .lower()
                    .replace(" ", "")
                    .replace("×", "x")
                )

                if dimension in normalized_print_size:
                    return print_size

    # Dla nazw typu „Nadruk standardowy”
    # przyjmujemy najmniejszy dostępny nadruk.
    if "standard" in normalized_size:

        return min(
            print_only_prices,
            key=lambda key: float(
                print_only_prices[key]
            )
        )

    raise ValueError(
        "Nie można dopasować ceny dodatkowego "
        f"nadruku dla wariantu: {selected_size}."
    )


def get_additional_print_price(
    prices,
    selected_size
):
    """
    Zwraca cenę dodatkowego nadruku
    oraz dopasowaną pozycję cennika.
    """

    print_only_prices = get_print_only_prices(
        prices
    )

    matched_size = find_print_only_size(
        selected_size,
        print_only_prices
    )

    additional_price = float(
        print_only_prices[
            matched_size
        ]
    )

    return {
        "price": additional_price,
        "matched_size": matched_size
    }


def calculate_apparel(
    category,
    product,
    front_print_size,
    back_print_size,
    quantity
):
    """
    Oblicza cenę odzieży z nadrukiem
    z osobnym nadrukiem z przodu i z tyłu.
    """

    if quantity <= 0:
        raise ValueError(
            "Ilość musi być większa od zera."
        )

    prices = load_prices()

    apparel_root = prices[
        "odziez_z_nadrukiem"
    ]

    apparel_data = apparel_root[
        "produkty"
    ]

    if category not in apparel_data:
        raise ValueError(
            "Nie znaleziono wybranej kategorii odzieży."
        )

    if product not in apparel_data[category]:
        raise ValueError(
            "Nie znaleziono wybranego produktu."
        )

    product_data = apparel_data[
        category
    ][
        product
    ]

    product_prices = product_data[
        "ceny"
    ]

    selected_prints = []

    if (
        front_print_size
        and front_print_size != NO_PRINT
    ):
        selected_prints.append(
            {
                "side": "Przód",
                "size": front_print_size
            }
        )

    if (
        back_print_size
        and back_print_size != NO_PRINT
    ):
        selected_prints.append(
            {
                "side": "Tył",
                "size": back_print_size
            }
        )

    if not selected_prints:
        raise ValueError(
            "Wybierz nadruk z przodu, z tyłu "
            "lub po obu stronach."
        )

    # Pierwszy wybrany nadruk korzysta z ceny
    # produktu razem z odzieżą.
    base_print = selected_prints[0]

    base_print_size = base_print[
        "size"
    ]

    if base_print_size not in product_prices:
        raise ValueError(
            "Nie znaleziono ceny wybranego "
            "rozmiaru nadruku."
        )

    base_unit_price = float(
        product_prices[
            base_print_size
        ]
    )

    extra_print_price = 0.0
    extra_print_side = None
    extra_print_size = None
    extra_print_matched_size = None

    # Drugi nadruk jest liczony według
    # cennika „Sam nadruk”.
    if len(selected_prints) > 1:

        extra_print = selected_prints[1]

        additional_print = (
            get_additional_print_price(
                prices,
                extra_print["size"]
            )
        )

        extra_print_price = float(
            additional_print["price"]
        )

        extra_print_side = extra_print[
            "side"
        ]

        extra_print_size = extra_print[
            "size"
        ]

        extra_print_matched_size = (
            additional_print[
                "matched_size"
            ]
        )

    unit_price = (
        base_unit_price
        + extra_print_price
    )

    discount_percent = get_apparel_discount(
        quantity,
        apparel_root.get(
            "rabaty",
            {}
        )
    )

    price_before_discount = (
        unit_price
        * quantity
    )

    discount_amount = (
        price_before_discount
        * discount_percent
        / 100
    )

    final_price = (
        price_before_discount
        - discount_amount
    )

    return {
        "price": round(
            final_price,
            2
        ),

        "unit_price": round(
            unit_price,
            2
        ),

        "base_unit_price": round(
            base_unit_price,
            2
        ),

        "extra_print_price": round(
            extra_print_price,
            2
        ),

        "quantity": quantity,

        "discount_percent": (
            discount_percent
        ),

        "discount_amount": round(
            discount_amount,
            2
        ),

        "price_before_discount": round(
            price_before_discount,
            2
        ),

        "description": product_data.get(
            "opis",
            ""
        ),

        "category": category,
        "product": product,

        "front_print_size": front_print_size,
        "back_print_size": back_print_size,

        "base_print_side": base_print[
            "side"
        ],

        "base_print_size": base_print_size,

        "extra_print_side": (
            extra_print_side
        ),

        "extra_print_size": (
            extra_print_size
        ),

        "extra_print_matched_size": (
            extra_print_matched_size
        )
    }
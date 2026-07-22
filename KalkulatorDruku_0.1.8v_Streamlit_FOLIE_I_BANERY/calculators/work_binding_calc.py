import math

from calculators.loader import load_prices


def get_print_tier(quantity):
    """
    Zwraca próg cenowy druku cyfrowego
    na podstawie łącznej liczby drukowanych stron.
    """

    if quantity <= 0:
        raise ValueError(
            "Liczba drukowanych stron musi być większa od zera."
        )

    if quantity <= 20:
        return "1-20"

    if quantity <= 100:
        return "21-100"

    if quantity <= 500:
        return "101-500"

    return "501+"


def calculate_work_binding(
    pages_per_copy,
    copies,
    color_mode,
    side_mode,
    binding_type,
    binding_variant
):
    """
    Oblicza druk cyfrowy A4 oraz oprawę prac.

    pages_per_copy:
        liczba stron jednego dokumentu

    copies:
        liczba oprawianych egzemplarzy

    side_mode:
        Jednostronny lub Dwustronny
    """

    if pages_per_copy <= 0:
        raise ValueError(
            "Liczba stron musi być większa od zera."
        )

    if copies <= 0:
        raise ValueError(
            "Liczba egzemplarzy musi być większa od zera."
        )

    prices = load_prices()

    digital_prices = prices[
        "druk_cyfrowy_i_ksero"
    ][
        "druk_cyfrowy"
    ]

    binding_prices = prices[
        "oprawa_prac"
    ][
        "rodzaje_opraw"
    ]

    if color_mode not in digital_prices:
        raise ValueError(
            "Nie znaleziono wybranego trybu kolorystycznego."
        )

    if side_mode not in (
        "Jednostronny",
        "Dwustronny"
    ):
        raise ValueError(
            "Nieprawidłowy sposób zadruku."
        )

    if binding_type not in binding_prices:
        raise ValueError(
            "Nie znaleziono wybranego rodzaju oprawy."
        )

    if (
        binding_variant
        not in binding_prices[binding_type]
    ):
        raise ValueError(
            "Nie znaleziono wybranego rozmiaru oprawy."
        )

    # Każda strona dokumentu to jedna drukowana strona A4.
    total_printed_pages = (
        pages_per_copy
        * copies
    )

    tier = get_print_tier(
        total_printed_pages
    )

    print_price_per_page = float(
        digital_prices[
            color_mode
        ][
            tier
        ]
    )

    print_total = (
        total_printed_pages
        * print_price_per_page
    )

    # Przy druku dwustronnym dwie strony dokumentu
    # mieszczą się na jednej kartce papieru.
    if side_mode == "Dwustronny":

        sheets_per_copy = math.ceil(
            pages_per_copy / 2
        )

    else:

        sheets_per_copy = pages_per_copy

    total_sheets = (
        sheets_per_copy
        * copies
    )

    binding_price_per_copy = float(
        binding_prices[
            binding_type
        ][
            binding_variant
        ]
    )

    binding_total = (
        binding_price_per_copy
        * copies
    )

    total_price = (
        print_total
        + binding_total
    )

    price_per_copy = (
        total_price
        / copies
    )

    return {
        "price": round(total_price, 2),

        "pages_per_copy": pages_per_copy,
        "copies": copies,
        "total_printed_pages": total_printed_pages,

        "side_mode": side_mode,
        "sheets_per_copy": sheets_per_copy,
        "total_sheets": total_sheets,

        "color_mode": color_mode,
        "tier": tier,
        "print_price_per_page": round(
            print_price_per_page,
            2
        ),
        "print_total": round(
            print_total,
            2
        ),

        "binding_type": binding_type,
        "binding_variant": binding_variant,
        "binding_price_per_copy": round(
            binding_price_per_copy,
            2
        ),
        "binding_total": round(
            binding_total,
            2
        ),

        "price_per_copy": round(
            price_per_copy,
            2
        )
    }

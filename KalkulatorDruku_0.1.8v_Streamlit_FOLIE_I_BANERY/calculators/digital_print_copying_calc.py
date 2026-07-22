from calculators.loader import load_prices


def get_quantity_tier(quantity):

    if quantity <= 0:
        raise ValueError(
            "Ilość musi być większa od zera."
        )

    if quantity <= 20:
        return "1-20"

    if quantity <= 100:
        return "21-100"

    if quantity <= 500:
        return "101-500"

    return "501+"


def calculate_digital_print_copying(
    service,
    color_mode,
    quantity,
    format_name="A4",
    paper_type="Standardowy 80 g",
    side_mode="Jednostronny"
):

    if quantity <= 0:
        raise ValueError(
            "Ilość musi być większa od zera."
        )

    prices = load_prices()[
        "druk_cyfrowy_i_ksero"
    ]

    if service in (
        "Druk cyfrowy",
        "Ksero i druk"
    ):

        if service == "Druk cyfrowy":
            service_prices = prices[
                "druk_cyfrowy"
            ]

            side_multiplier = float(
                prices[
                    "mnozniki_zadruku"
                ][
                    side_mode
                ]
            )
        else:
            service_prices = prices[
                "ksero_i_druk"
            ]

            side_multiplier = 1.0

        format_multiplier = float(
            prices[
                "mnozniki_formatu"
            ][
                format_name
            ]
        )

        # Liczba faktycznych zadruków po przeliczeniu na A4.
        # To ona decyduje o progu cenowym.
        # Przykład: 20 arkuszy A4 dwustronnie = 40 zadruków A4.
        print_units = (
            quantity
            * side_multiplier
            * format_multiplier
        )

        tier = get_quantity_tier(
            print_units
        )

        base_print_price = float(
            service_prices[
                color_mode
            ][
                tier
            ]
        )

        paper_surcharge = float(
            prices[
                "doplaty_do_papieru"
            ][
                paper_type
            ]
        )

        # Koszt druku jest liczony od wszystkich zadrukowanych stron.
        print_total = (
            base_print_price
            * print_units
        )

        # Papier jest doliczany tylko raz za każdy fizyczny arkusz.
        # Druk dwustronny nie zwiększa liczby arkuszy papieru.
        paper_units = (
            quantity
            * format_multiplier
        )

        paper_total = (
            paper_surcharge
            * paper_units
        )

        total = (
            print_total
            + paper_total
        )

    elif service == "Ksero książki":

        unit_price = float(
            prices[
                "ksero_ksiazki"
            ][
                color_mode
            ]
        )

        total = unit_price * quantity

    elif service == "Dla studentów":

        unit_price = float(
            prices[
                "dla_studentow"
            ][
                color_mode
            ][
                format_name
            ]
        )

        total = unit_price * quantity

    elif service == "Skanowanie":

        unit_price = float(
            prices[
                "skanowanie"
            ][
                color_mode
            ]
        )

        total = unit_price * quantity

    else:

        raise ValueError(
            "Nieobsługiwany rodzaj usługi."
        )

    return round(total, 2)

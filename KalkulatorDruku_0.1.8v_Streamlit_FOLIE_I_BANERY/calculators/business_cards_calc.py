from calculators.loader import load_prices


DIGITAL_FINISH_KEYS = {
    "Standard": "standard",
    "Folia Soft Touch lub błysk": "folia_soft_touch_lub_blysk"
}

OFFSET_FINISH_KEYS = {
    "Standard dwustronne": "standard_dwustronne",
    "Foliowane błysk lub Soft Touch":
        "foliowane_blysk_lub_soft_touch",
    "Złocenie lub srebrzenie + Soft Touch":
        "zlocenie_lub_srebrzenie_plus_soft_touch",
    "Lakier UV 3D + Soft Touch":
        "lakier_uv_3d_plus_soft_touch"
}

SIDE_KEYS = {
    "Jednostronne": "jednostronne",
    "Dwustronne": "dwustronne"
}


def calculate_business_cards(
    print_type,
    finish,
    quantity,
    sides
):
    prices = load_prices()

    quantity_key = str(quantity)

    if print_type == "Cyfrowy":
        finish_key = DIGITAL_FINISH_KEYS[finish]
        side_key = SIDE_KEYS[sides]

        price = prices["wizytowki"]["cyfrowe"][
            finish_key
        ][quantity_key][side_key]

    elif print_type == "Offsetowy":
        finish_key = OFFSET_FINISH_KEYS[finish]

        price = prices["wizytowki"]["offsetowe"][
            finish_key
        ][quantity_key]

    else:
        raise ValueError("Nieobsługiwany rodzaj druku.")

    return round(float(price), 2)
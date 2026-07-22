from typing import Optional

from calculators.loader import load_prices


def get_banner_price_per_m2(
    total_area: float,
    material: str,
    banner_data: Optional[dict] = None,
) -> float:
    """Zwraca cenę za 1 m² na podstawie łącznej powierzchni zamówienia."""

    if total_area <= 0:
        raise ValueError("Łączna powierzchnia musi być większa od zera.")

    if banner_data is None:
        prices = load_prices()
        banner_data = prices["banery"][material]

    price_tiers = banner_data.get("progi_cenowe", [])

    for tier in price_tiers:
        maximum_area = tier.get("maks_m2")
        if maximum_area is None or total_area <= float(maximum_area):
            return float(tier["cena_m2"])

    # Zgodność ze starszym cennikiem bez progów cenowych.
    return float(banner_data["cena_m2"])


def calculate_banner(
    width: float,
    height: float,
    quantity: int,
    material: str,
) -> float:
    """
    Oblicza cenę brutto zamówienia banerów.

    width i height podawane są w centymetrach.
    Cena za m² zależy od łącznej powierzchni zamówienia i progów
    zapisanych w data/prices.json.
    """

    if width <= 0:
        raise ValueError("Szerokość musi być większa od zera.")

    if height <= 0:
        raise ValueError("Wysokość musi być większa od zera.")

    if quantity <= 0:
        raise ValueError("Ilość musi być większa od zera.")

    prices = load_prices()
    banner_data = prices["banery"][material]
    minimum_order = float(banner_data["minimum_zamowienia"])

    width_m = width / 100
    height_m = height / 100

    area_one_piece = width_m * height_m
    total_area = area_one_piece * quantity

    price_m2 = get_banner_price_per_m2(
        total_area,
        material,
        banner_data,
    )
    calculated_price = total_area * price_m2
    final_price = max(calculated_price, minimum_order)

    return round(final_price, 2)

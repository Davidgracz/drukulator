import json
import os
import sys


def get_application_directory():
    """
    W czasie pracy z kodu zwraca główny folder projektu.

    W wersji EXE zwraca folder, w którym znajduje się
    KalkulatorDruku.exe.
    """

    if getattr(sys, "frozen", False):
        return os.path.dirname(
            sys.executable
        )

    return os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )


def get_prices_path():
    """
    Zwraca pełną ścieżkę do data/prices.json.
    """

    application_directory = (
        get_application_directory()
    )

    prices_path = os.path.join(
        application_directory,
        "data",
        "prices.json"
    )

    return prices_path


def load_prices():
    """
    Wczytuje cennik z pliku data/prices.json.
    """

    prices_path = get_prices_path()

    if not os.path.exists(prices_path):
        raise FileNotFoundError(
            "Nie znaleziono pliku cennika:\n"
            f"{prices_path}"
        )

    with open(
        prices_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)
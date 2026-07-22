# Kalkulator Druku 0.1.8v — Streamlit

Wersja przeglądarkowa przygotowana bezpośrednio na podstawie projektu `KalkulatorDruku_0.1.1v`.

## Zawartość

- Wizytówki
- Ulotki
- Banery
- Naklejki
- Plakaty
- Roll-up i X-baner
- PVC
- Druk cyfrowy, ksero i skanowanie
- Koszulki i odzież z nadrukiem
- Oprawa prac
- Laminowanie
- Obrazy na płótnie z wczytywaniem zdjęcia
- Koszyk i eksport wyceny do CSV
- Formularz zamówienia generujący gotowy tekst do skopiowania i wysłania mailem

## Uruchomienie na Windows

1. Rozpakuj cały folder.
2. Uruchom `start.bat`.
3. Aplikacja otworzy się pod adresem `http://localhost:8501`.

Skrypt najpierw próbuje użyć Pythona 3.8, a jeżeli go nie znajdzie, używa domyślnego polecenia `py`.

## Uruchomienie w sieci lokalnej

Uruchom `start_siec_lokalna.bat`, a na drugim komputerze wpisz w przeglądarce:

```text
http://ADRES_IP_KOMPUTERA:8501
```

## Ręczne uruchomienie

```powershell
py -3.8 -m pip install -r requirements.txt
py -3.8 -m streamlit run app.py
```

## Cennik

Wszystkie ceny znajdują się w pliku:

```text
data/prices.json
```


## Problem z plikiem BAT

Jeśli Windows blokuje `start.bat`, uruchom identyczny plik `start.cmd`. Oba skrypty są zapisane w formacie CRLF zgodnym z Windows.


## Zmiany w 0.1.8v

- Dodano progi cenowe banerów zależne od łącznej powierzchni.
- Podsumowanie pokazuje rzeczywistą stawkę za m² zamiast stałych 70 zł/m².
- Progi: do 3 m² — 80 zł, do 9 m² — 70 zł, do 20 m² — 60 zł, powyżej 20 m² — 50 zł.


## Zmiany w 0.1.8v

- Dodano formularz zamówienia w koszyku.
- Dodano pola: imię i nazwisko / firma, e-mail, telefon, sposób odbioru i uwagi.
- Treść maila jest automatycznie generowana z pozycji koszyka, parametrów produktów i sumy brutto.
- Temat i treść wiadomości można skopiować ikoną w prawym górnym rogu pola tekstowego.

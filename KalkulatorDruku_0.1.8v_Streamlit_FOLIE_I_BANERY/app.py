import csv
import io
from collections import OrderedDict

import streamlit as st
from PIL import Image, UnidentifiedImageError

from calculators.apparel_calc import NO_PRINT, calculate_apparel
from calculators.banner_calc import calculate_banner, get_banner_price_per_m2
from calculators.business_cards_calc import (
    DIGITAL_FINISH_KEYS,
    OFFSET_FINISH_KEYS,
    calculate_business_cards,
)
from calculators.canvas_print_calc import (
    calculate_canvas_print,
    calculate_custom_canvas_print,
    calculate_proportional_canvas_size,
    get_canvas_suggestions,
)
from calculators.digital_print_copying_calc import calculate_digital_print_copying
from calculators.flyers_calc import calculate_flyers
from calculators.lamination_calc import calculate_lamination
from calculators.loader import load_prices
from calculators.posters_calc import calculate_posters
from calculators.pvc_calc import calculate_pvc
from calculators.rollup_calc import calculate_rollup
from calculators.stickers_calc import calculate_stickers
from calculators.work_binding_calc import calculate_work_binding


APP_VERSION = "0.1.8v — Streamlit"

st.set_page_config(
    page_title="Drukulator",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stApp { background: #0B1120; }
        [data-testid="stSidebar"] { background: #111827; }
        [data-testid="stMetric"] {
            background: #151E2E;
            border: 1px solid #263449;
            border-radius: 12px;
            padding: 14px 16px;
        }
        div[data-testid="stForm"] {
            background: #151E2E;
            border: 1px solid #263449;
            border-radius: 14px;
            padding: 18px;
        }
        .quote-card {
            background: #151E2E;
            border: 1px solid #263449;
            border-radius: 14px;
            padding: 18px;
            margin-top: 18px;
        }
        .muted { color: #94A3B8; }
        .price-big {
            color: #F8FAFC;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.15;
        }
        .cart-card {
            background: #151E2E;
            border: 1px solid #263449;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 10px;
        }
        .block-container { padding-top: 1.5rem; }
        #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def get_prices():
    return load_prices()


PRICES = get_prices()


def init_state():
    if "cart" not in st.session_state:
        st.session_state.cart = []
    if "quotes" not in st.session_state:
        st.session_state.quotes = {}
    if "cart_counter" not in st.session_state:
        st.session_state.cart_counter = 0


def format_price(value):
    return f"{float(value):,.2f}".replace(",", " ").replace(".", ",")


def format_number(value, digits=2):
    return f"{float(value):.{digits}f}".replace(".", ",")


def safe_selectbox(label, options, key, **kwargs):
    options = list(options)
    if not options:
        raise ValueError(f"Brak opcji dla pola: {label}.")
    if key in st.session_state and st.session_state[key] not in options:
        del st.session_state[key]
    return st.selectbox(label, options, key=key, **kwargs)


def clear_quote(page):
    st.session_state.quotes.pop(page, None)


def save_quote(page, title, description, price, details, fingerprint):
    st.session_state.quotes[page] = {
        "title": title,
        "description": description,
        "price": round(float(price), 2),
        "details": OrderedDict(details),
        "fingerprint": tuple(fingerprint),
    }


def build_order_email_text(customer_name, customer_email, customer_phone, pickup_method, notes):
    total = sum(item["price"] for item in st.session_state.cart)

    lines = [
        "Dzień dobry,",
        "",
        "proszę o realizację poniższego zamówienia:",
        "",
    ]

    for index, item in enumerate(st.session_state.cart, start=1):
        lines.append(f"{index}. {item['title']}")
        lines.append(f"   {item['description']}")

        for label, value in item.get("details", {}).items():
            lines.append(f"   {label}: {value}")

        lines.append(f"   Cena brutto: {format_price(item['price'])} zł")
        lines.append("")

    lines.extend([
        f"RAZEM BRUTTO: {format_price(total)} zł",
        "",
        "Dane zamawiającego:",
        f"Imię i nazwisko / firma: {customer_name or '—'}",
        f"E-mail: {customer_email or '—'}",
        f"Telefon: {customer_phone or '—'}",
        f"Sposób odbioru: {pickup_method}",
    ])

    if notes.strip():
        lines.extend([
            "",
            "Uwagi do zamówienia:",
            notes.strip(),
        ])

    lines.extend([
        "",
        "Proszę o potwierdzenie ceny, terminu realizacji oraz sposobu przekazania plików.",
        "",
        "Pozdrawiam,",
        customer_name or "",
    ])

    return "\n".join(lines).rstrip()


def render_order_form():
    st.divider()
    st.subheader("Formularz zamówienia")
    st.caption("Uzupełnij dane, a następnie skopiuj gotową wiadomość do maila.")

    customer_name = st.text_input(
        "Imię i nazwisko / firma",
        key="order_customer_name",
        placeholder="np. Jan Kowalski / Firma ABC",
    )
    customer_email = st.text_input(
        "E-mail",
        key="order_customer_email",
        placeholder="np. kontakt@firma.pl",
    )
    customer_phone = st.text_input(
        "Telefon",
        key="order_customer_phone",
        placeholder="np. 500 000 000",
    )
    pickup_method = st.selectbox(
        "Sposób odbioru",
        ["Odbiór osobisty", "Wysyłka kurierska", "Do ustalenia"],
        key="order_pickup_method",
    )
    notes = st.text_area(
        "Uwagi do zamówienia",
        key="order_notes",
        placeholder="Np. oczekiwany termin, sposób pakowania, dodatkowe informacje...",
        height=100,
    )

    subject = "Zamówienie z kalkulatora Druk24"
    email_text = build_order_email_text(
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        pickup_method=pickup_method,
        notes=notes,
    )

    st.markdown("**Temat wiadomości:**")
    st.code(subject, language=None)
    st.markdown("**Treść wiadomości:**")
    st.code(email_text, language=None)
    st.caption("Kliknij ikonę kopiowania w prawym górnym rogu pola tekstowego.")


def cart_csv_bytes():
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Lp.", "Produkt", "Opis", "Cena brutto"])
    for index, item in enumerate(st.session_state.cart, start=1):
        writer.writerow([
            index,
            item["title"],
            item["description"],
            f'{item["price"]:.2f}'.replace(".", ","),
        ])
    writer.writerow([])
    writer.writerow([
        "",
        "RAZEM",
        "",
        f'{sum(item["price"] for item in st.session_state.cart):.2f}'.replace(".", ","),
    ])
    return output.getvalue().encode("utf-8-sig")


def render_cart():
    st.subheader("Koszyk")

    if not st.session_state.cart:
        st.info("Koszyk jest pusty.")
        return

    for index, item in enumerate(st.session_state.cart):
        st.markdown(
            f"""
            <div class="cart-card">
                <strong>{index + 1}. {item['title']}</strong><br>
                <span class="muted">{item['description']}</span><br>
                <strong>{format_price(item['price'])} zł</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Usuń", key=f"remove_cart_{item['id']}", use_container_width=True):
            st.session_state.cart.pop(index)
            st.rerun()

    total = sum(item["price"] for item in st.session_state.cart)
    st.metric("Razem brutto", f"{format_price(total)} zł")

    st.download_button(
        "Pobierz koszyk CSV",
        data=cart_csv_bytes(),
        file_name="wycena_kalkulator_druku.csv",
        mime="text/csv",
        use_container_width=True,
    )

    if st.button("Wyczyść koszyk", type="secondary", use_container_width=True):
        st.session_state.cart = []
        st.rerun()

    render_order_form()


def render_quote(page, current_fingerprint):
    quote = st.session_state.quotes.get(page)
    if quote is None:
        st.caption("Uzupełnij parametry i kliknij „Oblicz cenę”.")
        return

    is_current = tuple(current_fingerprint) == tuple(quote["fingerprint"])
    if not is_current:
        st.warning("Parametry zostały zmienione. Oblicz cenę ponownie.")
        return

    st.markdown('<div class="quote-card">', unsafe_allow_html=True)
    st.caption(quote["title"])
    st.markdown(
        f'<div class="price-big">Cena brutto: {format_price(quote["price"])} zł</div>',
        unsafe_allow_html=True,
    )
    st.write(quote["description"])

    if quote["details"]:
        with st.expander("Szczegóły obliczenia", expanded=True):
            for label, value in quote["details"].items():
                st.write(f"**{label}:** {value}")

    if st.button(
        "Dodaj do koszyka",
        type="primary",
        use_container_width=True,
        key=f"add_quote_{page}",
    ):
        st.session_state.cart_counter += 1
        cart_item = dict(quote)
        cart_item["id"] = st.session_state.cart_counter
        cart_item.pop("fingerprint", None)
        st.session_state.cart.append(cart_item)
        st.success("Dodano do koszyka.")

    st.markdown("</div>", unsafe_allow_html=True)


def render_header(title, subtitle="Uzupełnij parametry i oblicz cenę brutto"):
    st.title(title)
    st.caption(subtitle)


def render_business_cards():
    page = "Wizytówki"
    render_header(page)

    formats = PRICES["wizytowki"]["formaty"]
    format_name = safe_selectbox("Format", formats, "bc_format")
    print_type = safe_selectbox("Rodzaj druku", ["Cyfrowy", "Offsetowy"], "bc_print")

    if print_type == "Cyfrowy":
        finish_options = list(DIGITAL_FINISH_KEYS.keys())
        finish = safe_selectbox("Wykończenie", finish_options, "bc_finish_digital")
        sides = safe_selectbox("Zadruk", ["Jednostronne", "Dwustronne"], "bc_sides")
        finish_key = DIGITAL_FINISH_KEYS[finish]
        quantities = list(PRICES["wizytowki"]["cyfrowe"][finish_key].keys())
    else:
        finish_options = list(OFFSET_FINISH_KEYS.keys())
        finish = safe_selectbox("Wykończenie", finish_options, "bc_finish_offset")
        sides = "Dwustronne"
        st.selectbox("Zadruk", [sides], disabled=True, key="bc_sides_offset")
        finish_key = OFFSET_FINISH_KEYS[finish]
        quantities = list(PRICES["wizytowki"]["offsetowe"][finish_key].keys())

    quantity_text = safe_selectbox("Nakład", quantities, "bc_quantity")
    quantity = int(quantity_text)
    fingerprint = (format_name, print_type, finish, sides, quantity)

    if st.button("Oblicz cenę", type="primary", key="bc_calculate"):
        try:
            price = calculate_business_cards(print_type, finish, quantity, sides)
            save_quote(
                page,
                page,
                f"{format_name}, druk {print_type.lower()}, {finish}, {sides.lower()}, {quantity} szt.",
                price,
                [("Format", format_name), ("Nakład", f"{quantity} szt.")],
                fingerprint,
            )
        except Exception as error:
            clear_quote(page)
            st.error(str(error))

    render_quote(page, fingerprint)


def render_flyers():
    page = "Ulotki"
    render_header(page, "Papier 130 g, kolor dwustronny")

    root = PRICES["ulotki"]
    print_type = safe_selectbox("Rodzaj druku", root.keys(), "fly_print")
    variant = safe_selectbox("Rodzaj ulotki", root[print_type].keys(), "fly_variant")
    format_name = safe_selectbox("Format", root[print_type][variant].keys(), "fly_format")
    quantities = root[print_type][variant][format_name].keys()
    quantity = int(safe_selectbox("Nakład", quantities, "fly_quantity"))
    fingerprint = (print_type, variant, format_name, quantity)

    if st.button("Oblicz cenę", type="primary", key="fly_calculate"):
        try:
            price = calculate_flyers(print_type, variant, format_name, quantity)
            save_quote(
                page,
                page,
                f"{print_type}, {variant}, format {format_name}, {quantity} szt.",
                price,
                [("Papier", "130 g"), ("Zadruk", "Kolor dwustronny")],
                fingerprint,
            )
        except Exception as error:
            clear_quote(page)
            st.error(str(error))

    render_quote(page, fingerprint)


def render_banners():
    page = "Folie i banery"
    render_header(page, "Wycena na podstawie łącznej powierzchni zamówienia")

    materials = PRICES["banery"].keys()
    material = safe_selectbox("Materiał", materials, "banner_material")
    col1, col2, col3 = st.columns(3)
    with col1:
        width = st.number_input("Szerokość [cm]", min_value=0.1, value=100.0, step=1.0, key="banner_width")
    with col2:
        height = st.number_input("Wysokość [cm]", min_value=0.1, value=200.0, step=1.0, key="banner_height")
    with col3:
        quantity = st.number_input("Ilość sztuk", min_value=1, value=1, step=1, key="banner_quantity")

    material_data = PRICES["banery"][material]
    if material_data.get("oczka_w_standardzie"):
        st.success("✓ Oczka w standardzie")

    area = width / 100 * height / 100 * int(quantity)
    fingerprint = (material, float(width), float(height), int(quantity))

    with st.expander("Progi cenowe materiału"):
        previous_limit = 0.0
        for tier in material_data.get("progi_cenowe", []):
            maximum_area = tier.get("maks_m2")
            tier_price = format_price(tier["cena_m2"])
            if maximum_area is None:
                st.write(f"**Powyżej {previous_limit:g} m²:** {tier_price} zł/m²")
            elif previous_limit == 0:
                st.write(f"**Do {float(maximum_area):g} m²:** {tier_price} zł/m²")
            else:
                st.write(
                    f"**Powyżej {previous_limit:g} do {float(maximum_area):g} m²:** "
                    f"{tier_price} zł/m²"
                )
            if maximum_area is not None:
                previous_limit = float(maximum_area)

    if st.button("Oblicz cenę", type="primary", key="banner_calculate"):
        try:
            unit_price = get_banner_price_per_m2(
                area,
                material,
                material_data,
            )
            price = calculate_banner(width, height, int(quantity), material)
            save_quote(
                page,
                material,
                f"{material}, {width:g} × {height:g} cm, {int(quantity)} szt.",
                price,
                [
                    ("Łączna powierzchnia", f"{format_number(area)} m²"),
                    ("Cena za m²", f"{format_price(unit_price)} zł"),
                    ("Minimum zamówienia", f"{format_price(material_data['minimum_zamowienia'])} zł"),
                ],
                fingerprint,
            )
        except Exception as error:
            clear_quote(page)
            st.error(str(error))

    render_quote(page, fingerprint)


def render_stickers():
    page = "Naklejki"
    render_header(page)

    root = PRICES["naklejki"]
    surface_products = list(root["powierzchniowe"].keys())
    taxi_products = list(root["taxi"].keys())
    product_type = safe_selectbox(
        "Rodzaj produktu",
        surface_products + taxi_products,
        "stick_product",
    )

    is_surface = product_type in root["powierzchniowe"]
    if is_surface:
        col1, col2, col3 = st.columns(3)
        with col1:
            width_mm = st.number_input(
                "Szerokość jednej sztuki [mm]",
                min_value=1.0,
                value=100.0,
                step=1.0,
                key="stick_width_mm",
            )
        with col2:
            height_mm = st.number_input(
                "Wysokość jednej sztuki [mm]",
                min_value=1.0,
                value=100.0,
                step=1.0,
                key="stick_height_mm",
            )
        with col3:
            quantity = st.number_input("Minimalna liczba naklejek", min_value=1, value=100, step=1, key="stick_quantity")

        # Funkcja calculate_stickers nadal przyjmuje wymiary w centymetrach,
        # dlatego wartości podane przez użytkownika w mm są przeliczane na cm.
        width_cm = float(width_mm) / 10.0
        height_cm = float(height_mm) / 10.0

        minimum = root["powierzchniowe"][product_type]["minimum_m2"]
        st.info(f"Minimalne zamówienie: {format_number(minimum, 1)} mb. Szerokość folii: 1000 mm.")
    else:
        width_mm = None
        height_mm = None
        width_cm = None
        height_cm = None
        quantity = st.number_input("Ilość kompletów / sztuk", min_value=1, value=1, step=1, key="stick_quantity_taxi")

    fingerprint = (product_type, int(quantity), width_mm, height_mm)

    if st.button("Oblicz cenę", type="primary", key="stick_calculate"):
        try:
            result = calculate_stickers(product_type, int(quantity), width_cm, height_cm)
            details = []
            description = f"{product_type}, {int(quantity)} zamówionych szt./kompletów"
            if is_surface:
                description = f"{product_type}, {width_mm:g} × {height_mm:g} mm, minimum {int(quantity)} szt."
                details = [
                    ("Naklejek w rzędzie", str(result["stickers_per_row"])),
                    ("Liczba rzędów", str(result["rows"])),
                    ("Łącznie wykonanych naklejek", str(result["total_stickers"])),
                    ("Dodatkowych naklejek", str(result["extra_stickers"])),
                    ("Długość przed zaokrągleniem", f"{format_number(result['base_length_m'], 3)} mb"),
                    ("Długość rozliczeniowa", f"{format_number(result['billed_length_m'], 1)} mb"),
                    ("Cena za mb", f"{format_price(result['price_per_linear_meter'])} zł"),
                    ("Wymiar produkcyjny", f"{format_number(result['production_width_mm'], 1)} × {format_number(result['production_height_mm'], 1)} mm"),
                ]
            else:
                unit_price = root["taxi"][product_type]["cena_sztuki"]
                details = [("Cena jednostkowa", f"{format_price(unit_price)} zł")]

            save_quote(page, product_type, description, result["price"], details, fingerprint)
        except Exception as error:
            clear_quote(page)
            st.error(str(error))

    render_quote(page, fingerprint)


def render_posters():
    page = "Plakaty"
    render_header(page)

    root = PRICES["plakaty"]
    print_type = safe_selectbox("Rodzaj druku", root.keys(), "poster_print")
    format_name = safe_selectbox("Format", root[print_type].keys(), "poster_format")

    if print_type == "Wielkoformatowy":
        quantity = int(st.number_input("Ilość sztuk", min_value=1, value=1, step=1, key="poster_quantity_large"))
        paper = "Papier satynowy 135 g"
    else:
        quantity = int(safe_selectbox("Nakład", root[print_type][format_name].keys(), "poster_quantity"))
        paper = "Papier 170 g, kolor jednostronny"

    fingerprint = (print_type, format_name, quantity)

    if st.button("Oblicz cenę", type="primary", key="poster_calculate"):
        try:
            price = calculate_posters(print_type, format_name, quantity)
            save_quote(
                page,
                page,
                f"{print_type}, format {format_name}, {quantity} szt.",
                price,
                [("Materiał", paper)],
                fingerprint,
            )
        except Exception as error:
            clear_quote(page)
            st.error(str(error))

    render_quote(page, fingerprint)


def render_rollup():
    page = "Roll-up"
    render_header("Roll-up i X-baner")

    root = PRICES["rollup"]
    product_type = safe_selectbox("Rodzaj produktu", root.keys(), "roll_product")
    size = safe_selectbox("Szerokość / format", root[product_type].keys(), "roll_size")
    quantity = int(st.number_input("Ilość sztuk", min_value=1, value=1, step=1, key="roll_quantity"))

    if product_type == "X-baner":
        st.caption("Format określony w wybranym wariancie.")
    else:
        st.caption("Wysokość roll-upu: 200 cm.")

    fingerprint = (product_type, size, quantity)

    if st.button("Oblicz cenę", type="primary", key="roll_calculate"):
        try:
            price = calculate_rollup(product_type, size, quantity)
            save_quote(
                page,
                product_type,
                f"{product_type}, {size}, {quantity} szt.",
                price,
                [("Cena jednostkowa", f"{format_price(root[product_type][size])} zł")],
                fingerprint,
            )
        except Exception as error:
            clear_quote(page)
            st.error(str(error))

    render_quote(page, fingerprint)


def render_pvc():
    page = "PVC"
    render_header("Druk na PCV")

    root = PRICES["pvc"]
    product_type = safe_selectbox("Rodzaj produktu", root.keys(), "pvc_product")
    product_data = root[product_type]
    thickness = safe_selectbox("Grubość płyty", product_data.get("grubosc", ["Nie dotyczy"]), "pvc_thickness")

    col1, col2, col3 = st.columns(3)
    with col1:
        width = st.number_input("Szerokość jednej sztuki [cm]", min_value=0.1, value=100.0, step=1.0, key="pvc_width")
    with col2:
        height = st.number_input("Wysokość jednej sztuki [cm]", min_value=0.1, value=50.0, step=1.0, key="pvc_height")
    with col3:
        quantity = int(st.number_input("Ilość sztuk", min_value=1, value=1, step=1, key="pvc_quantity"))

    area = width / 100 * height / 100 * quantity
    fingerprint = (product_type, thickness, float(width), float(height), quantity)

    if st.button("Oblicz cenę", type="primary", key="pvc_calculate"):
        try:
            price = calculate_pvc(width, height, quantity, product_type)
            save_quote(
                page,
                page,
                f"{product_type}, płyta {thickness}, {width:g} × {height:g} cm, {quantity} szt.",
                price,
                [
                    ("Łączna powierzchnia", f"{format_number(area)} m²"),
                    ("Cena za m²", f"{format_price(product_data['cena_m2'])} zł"),
                    ("Minimum zamówienia", f"{format_price(product_data['minimum_zamowienia'])} zł"),
                ],
                fingerprint,
            )
        except Exception as error:
            clear_quote(page)
            st.error(str(error))

    render_quote(page, fingerprint)


def render_digital_print():
    page = "Druk cyfrowy i ksero"
    render_header("Druk cyfrowy, ksero i skanowanie")

    root = PRICES["druk_cyfrowy_i_ksero"]
    services = ["Druk cyfrowy", "Ksero i druk", "Ksero książki", "Dla studentów", "Skanowanie"]
    service = safe_selectbox("Rodzaj usługi", services, "digital_service")

    standard_papers = [
        "Standardowy 80 g",
        "Papier kredowy 130 g",
        "Papier kredowy 170 g",
        "Papier kredowy 250 g",
        "Papier kredowy 300 g",
        "Papier kredowy 350 g",
    ]
    black_papers = [
        "Standardowy 80 g",
        "Papier kolorowy",
        "Papier etykietowy",
        "Papier kredowy 130 g",
        "Papier kredowy 170 g",
        "Papier kredowy 250 g",
        "Papier kredowy 300 g",
        "Papier kredowy 350 g",
    ]

    format_name = "Nie dotyczy"
    paper_type = "Nie dotyczy"
    side_mode = "Nie dotyczy"

    if service == "Druk cyfrowy":
        color_mode = safe_selectbox("Rodzaj druku", root["druk_cyfrowy"].keys(), "digital_color")
        format_name = safe_selectbox("Format", root["mnozniki_formatu"].keys(), "digital_format")
        side_mode = safe_selectbox("Zadruk", root["mnozniki_zadruku"].keys(), "digital_side")
        papers = black_papers if color_mode == "Czarno-biały" else standard_papers
        paper_type = safe_selectbox("Rodzaj papieru", papers, "digital_paper")
        quantity_label = "Liczba arkuszy"
        st.caption("Druk dwustronny: cena druku × 2. Koszt papieru jest doliczany tylko raz.")
    elif service == "Ksero i druk":
        color_mode = safe_selectbox("Rodzaj druku", root["ksero_i_druk"].keys(), "copy_color")
        format_name = safe_selectbox("Format", root["mnozniki_formatu"].keys(), "copy_format")
        paper_type = safe_selectbox("Rodzaj papieru", standard_papers, "copy_paper")
        quantity_label = "Liczba kopii"
        st.caption("Format A3 kosztuje 2 razy więcej niż format A4.")
    elif service == "Ksero książki":
        color_mode = safe_selectbox("Rodzaj druku", root["ksero_ksiazki"].keys(), "book_color")
        quantity_label = "Liczba stron"
        st.caption("Cena jest naliczana za każdą kopiowaną stronę.")
    elif service == "Dla studentów":
        color_mode = safe_selectbox("Rodzaj druku", root["dla_studentow"].keys(), "student_color")
        format_name = safe_selectbox("Format", root["dla_studentow"][color_mode].keys(), "student_format")
        paper_type = "Standardowy 80 g"
        quantity_label = "Liczba kopii"
        st.caption("Cennik studencki nie dotyczy kopiowania książek.")
    else:
        color_mode = safe_selectbox("Rodzaj skanowania", root["skanowanie"].keys(), "scan_mode")
        quantity_label = "Liczba skanowanych stron"
        st.caption("Cena jest taka sama dla skanów czarno-białych i kolorowych.")

    quantity = int(st.number_input(quantity_label, min_value=1, value=1, step=1, key="digital_quantity"))
    fingerprint = (service, color_mode, quantity, format_name, paper_type, side_mode)

    if st.button("Oblicz cenę", type="primary", key="digital_calculate"):
        try:
            price = calculate_digital_print_copying(
                service=service,
                color_mode=color_mode,
                quantity=quantity,
                format_name=format_name,
                paper_type=paper_type,
                side_mode=side_mode,
            )
            details = [("Rodzaj usługi", service), ("Wariant", color_mode), ("Ilość", str(quantity))]
            if format_name != "Nie dotyczy":
                details.append(("Format", format_name))
            if side_mode != "Nie dotyczy":
                details.append(("Zadruk", side_mode))
            if paper_type != "Nie dotyczy":
                details.append(("Papier", paper_type))
            save_quote(
                page,
                service,
                f"{service}, {color_mode}, {quantity} szt./stron",
                price,
                details,
                fingerprint,
            )
        except Exception as error:
            clear_quote(page)
            st.error(str(error))

    render_quote(page, fingerprint)


def render_apparel():
    page = "Koszulki i odzież"
    render_header("Koszulki i odzież z nadrukiem")

    apparel_root = PRICES["odziez_z_nadrukiem"]
    products_root = apparel_root["produkty"]
    category = safe_selectbox("Kategoria produktu", products_root.keys(), "apparel_category")
    product = safe_selectbox("Model", products_root[category].keys(), "apparel_product")
    product_data = products_root[category][product]
    print_sizes = list(product_data["ceny"].keys())
    menu_values = [NO_PRINT] + print_sizes

    col1, col2 = st.columns(2)
    with col1:
        front = safe_selectbox("Rozmiar nadruku z przodu", menu_values, "apparel_front")
    with col2:
        back = safe_selectbox("Rozmiar nadruku z tyłu", menu_values, "apparel_back")

    quantity = int(st.number_input("Ilość sztuk", min_value=1, value=1, step=1, key="apparel_quantity"))
    description = product_data.get("opis", "")
    if description:
        st.info(description)

    discounts = apparel_root.get("rabaty", {})
    st.caption(
        f"Rabat: {discounts.get('od_10_sztuk', 10)}% od 10 sztuk, "
        f"{discounts.get('powyzej_20_sztuk', 20)}% powyżej 20 sztuk."
    )

    fingerprint = (category, product, front, back, quantity)

    if st.button("Oblicz cenę", type="primary", key="apparel_calculate"):
        try:
            result = calculate_apparel(category, product, front, back, quantity)
            details = [
                ("Cena bazowa za sztukę", f"{format_price(result['base_unit_price'])} zł"),
                ("Dopłata za drugi nadruk", f"{format_price(result['extra_print_price'])} zł"),
                ("Cena jednostkowa przed rabatem", f"{format_price(result['unit_price'])} zł"),
                ("Wartość przed rabatem", f"{format_price(result['price_before_discount'])} zł"),
                ("Rabat", f"{format_number(result['discount_percent'], 0)}% = {format_price(result['discount_amount'])} zł"),
            ]
            if result.get("extra_print_matched_size"):
                details.append(("Drugi nadruk rozliczony jako", result["extra_print_matched_size"]))
            quote_description = (
                f"{category} — {product}, przód: {front}, tył: {back}, {quantity} szt."
            )
            save_quote(page, product, quote_description, result["price"], details, fingerprint)
        except Exception as error:
            clear_quote(page)
            st.error(str(error))

    render_quote(page, fingerprint)


def render_work_binding():
    page = "Oprawa prac"
    render_header("Druk i oprawa prac", "Druk cyfrowy A4 oraz oprawa dokumentu")

    root = PRICES["oprawa_prac"]["rodzaje_opraw"]
    digital = PRICES["druk_cyfrowy_i_ksero"]["druk_cyfrowy"]
    color_mode = safe_selectbox("Tryb druku", digital.keys(), "binding_color")
    side_mode = safe_selectbox("Sposób zadruku", ["Jednostronny", "Dwustronny"], "binding_side")

    col1, col2 = st.columns(2)
    with col1:
        pages = int(st.number_input("Liczba stron jednego dokumentu", min_value=1, value=80, step=1, key="binding_pages"))
    with col2:
        copies = int(st.number_input("Liczba egzemplarzy", min_value=1, value=1, step=1, key="binding_copies"))

    binding_type = safe_selectbox("Rodzaj oprawy", root.keys(), "binding_type")
    binding_variant = safe_selectbox("Rozmiar oprawy / spirali", root[binding_type].keys(), "binding_variant")
    fingerprint = (pages, copies, color_mode, side_mode, binding_type, binding_variant)

    if st.button("Oblicz cenę", type="primary", key="binding_calculate"):
        try:
            result = calculate_work_binding(
                pages_per_copy=pages,
                copies=copies,
                color_mode=color_mode,
                side_mode=side_mode,
                binding_type=binding_type,
                binding_variant=binding_variant,
            )
            details = [
                ("Łączna liczba drukowanych stron", str(result["total_printed_pages"])),
                ("Łączna liczba arkuszy", str(result["total_sheets"])),
                ("Próg cenowy druku", result["tier"]),
                ("Koszt druku", f"{format_price(result['print_total'])} zł"),
                ("Koszt opraw", f"{format_price(result['binding_total'])} zł"),
                ("Cena jednego egzemplarza", f"{format_price(result['price_per_copy'])} zł"),
            ]
            save_quote(
                page,
                page,
                f"{copies} egz., po {pages} stron, {color_mode}, {side_mode.lower()}, {binding_type} {binding_variant}",
                result["price"],
                details,
                fingerprint,
            )
        except Exception as error:
            clear_quote(page)
            st.error(str(error))

    render_quote(page, fingerprint)


def render_lamination():
    page = "Laminowanie"
    root = PRICES["laminowanie"]
    render_header(page, f"Laminowanie dokumentów folią {root.get('folia_mikrony', 80)} mikronów")

    format_name = safe_selectbox("Format dokumentu", root["formaty"].keys(), "lam_format")
    quantity = int(st.number_input("Ilość sztuk", min_value=1, value=1, step=1, key="lam_quantity"))
    fingerprint = (format_name, quantity)

    with st.expander("Cennik brutto"):
        for name, price in root["formaty"].items():
            st.write(f"**{name}:** {format_price(price)} zł / szt.")

    if st.button("Oblicz cenę", type="primary", key="lam_calculate"):
        try:
            result = calculate_lamination(format_name, quantity)
            save_quote(
                page,
                page,
                f"Format {format_name}, {quantity} szt., folia {result['foil_microns']} µm",
                result["price"],
                [("Cena jednostkowa", f"{format_price(result['unit_price'])} zł")],
                fingerprint,
            )
        except Exception as error:
            clear_quote(page)
            st.error(str(error))

    render_quote(page, fingerprint)


def render_canvas():
    page = "Obrazy na płótnie"
    root = PRICES["obrazy_na_plotnie"]
    render_header(page, f"{root.get('material', 'Płótno')}; maksymalny bok: {root.get('maksymalny_bok_cm', 150)} cm")

    uploaded = st.file_uploader(
        "Wybierz plik JPG / PNG",
        type=["jpg", "jpeg", "png", "tif", "tiff", "webp"],
        key="canvas_file",
    )

    if uploaded is None:
        clear_quote(page)
        st.info("Wczytaj zdjęcie, aby dopasować format do jego proporcji.")
        return

    try:
        uploaded.seek(0)
        image = Image.open(uploaded)
        image.load()
    except (UnidentifiedImageError, OSError) as error:
        clear_quote(page)
        st.error(f"Nie można odczytać pliku obrazu: {error}")
        return

    image_width, image_height = image.size
    st.image(image, caption=f"{uploaded.name} — {image_width} × {image_height} px", use_column_width=True)

    size_mode = safe_selectbox(
        "Sposób wyboru rozmiaru",
        ["Proponowane formaty", "Podaj jeden bok"],
        "canvas_mode",
    )
    quantity = int(st.number_input("Ilość obrazów", min_value=1, value=1, step=1, key="canvas_quantity"))

    file_fingerprint = (uploaded.name, uploaded.size, image_width, image_height)

    if size_mode == "Proponowane formaty":
        try:
            suggestions = get_canvas_suggestions(image_width, image_height)
        except Exception as error:
            clear_quote(page)
            st.error(str(error))
            return

        labels = []
        suggestion_map = {}
        for item in suggestions:
            label = (
                f"{item['display_width_cm']:g} × {item['display_height_cm']:g} cm "
                f"— {format_price(item['price'])} zł/szt. "
                f"— różnica proporcji {format_number(item['ratio_error_percent'], 2)}%"
            )
            labels.append(label)
            suggestion_map[label] = item

        selected_label = safe_selectbox("Proponowany format obrazu", labels, "canvas_suggestion")
        selected = suggestion_map[selected_label]
        fingerprint = file_fingerprint + (size_mode, selected_label, quantity)

        if st.button("Oblicz cenę", type="primary", key="canvas_calculate_standard"):
            try:
                result = calculate_canvas_print(selected["format_key"], quantity)
                description = (
                    f"{selected['display_width_cm']:g} × {selected['display_height_cm']:g} cm, "
                    f"{quantity} szt., plik {uploaded.name}"
                )
                details = [
                    ("Format cennikowy", result["format_key"]),
                    ("Cena jednostkowa", f"{format_price(result['unit_price'])} zł"),
                    ("Różnica proporcji", f"{format_number(selected['ratio_error_percent'], 2)}%"),
                    ("Rozdzielczość pliku", f"{image_width} × {image_height} px"),
                ]
                save_quote(page, page, description, result["price"], details, fingerprint)
            except Exception as error:
                clear_quote(page)
                st.error(str(error))

    else:
        known_side = safe_selectbox("Który bok podajesz?", ["Szerokość", "Wysokość"], "canvas_known_side")
        known_value = st.number_input(
            "Wartość podanego boku [cm]",
            min_value=0.1,
            value=60.0,
            step=0.1,
            key="canvas_known_value",
        )
        fingerprint = file_fingerprint + (size_mode, known_side, float(known_value), quantity)

        proportional = None
        try:
            proportional = calculate_proportional_canvas_size(
                image_width_px=image_width,
                image_height_px=image_height,
                known_side=known_side,
                known_value_cm=known_value,
            )
            st.success(
                f"Rozmiar z zachowaniem proporcji: "
                f"{proportional['width_cm']:.1f} × {proportional['height_cm']:.1f} cm"
            )
        except ValueError as error:
            st.warning(str(error))

        if st.button(
            "Oblicz cenę",
            type="primary",
            key="canvas_calculate_custom",
            disabled=proportional is None,
        ):
            try:
                result = calculate_custom_canvas_print(
                    width_cm=proportional["width_cm"],
                    height_cm=proportional["height_cm"],
                    quantity=quantity,
                )
                description = (
                    f"{result['custom_width_cm']:.1f} × {result['custom_height_cm']:.1f} cm, "
                    f"{quantity} szt., plik {uploaded.name}"
                )
                details = [
                    ("Format rozliczeniowy", result["billing_format_key"]),
                    ("Wymiar rozliczeniowy", f"{result['billing_width_cm']:g} × {result['billing_height_cm']:g} cm"),
                    ("Sposób rozliczenia", result["billing_method"]),
                    ("Cena jednostkowa", f"{format_price(result['unit_price'])} zł"),
                    ("Rozdzielczość pliku", f"{image_width} × {image_height} px"),
                ]
                save_quote(page, page, description, result["price"], details, fingerprint)
            except Exception as error:
                clear_quote(page)
                st.error(str(error))

    render_quote(page, fingerprint)


def render_home():
    render_header("Kalkulator Druku", "Wersja przeglądarkowa projektu 0.1.8v")
    st.markdown(
        """
        Wybierz produkt z menu po lewej stronie. Każdy kalkulator korzysta z tego samego
        pliku `data/prices.json`, co wersja desktopowa.
        """
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("Kalkulatory", "12")
    col2.metric("Ceny", "Brutto")
    col3.metric("Wersja", APP_VERSION)


init_state()

PAGES = OrderedDict([
    ("Start", render_home),
    ("Wizytówki", render_business_cards),
    ("Ulotki", render_flyers),
    ("Folie i banery", render_banners),
    ("Naklejki", render_stickers),
    ("Plakaty", render_posters),
    ("Roll-up", render_rollup),
    ("PVC", render_pvc),
    ("Druk cyfrowy i ksero", render_digital_print),
    ("Koszulki i odzież", render_apparel),
    ("Oprawa prac", render_work_binding),
    ("Laminowanie", render_lamination),
    ("Obrazy na płótnie", render_canvas),
])

with st.sidebar:
    st.markdown("## Drukulator")
    st.caption(APP_VERSION)
    selected_page = st.radio("Produkt", list(PAGES.keys()), label_visibility="collapsed")
    st.divider()
    st.download_button(
        "Pobierz prices.json",
        data=io.BytesIO(
            __import__("json").dumps(PRICES, ensure_ascii=False, indent=2).encode("utf-8")
        ),
        file_name="prices.json",
        mime="application/json",
        use_container_width=True,
    )

main_col, cart_col = st.columns([3.2, 1.15], gap="large")

with main_col:
    try:
        PAGES[selected_page]()
    except FileNotFoundError as error:
        st.error(str(error))
    except KeyError as error:
        st.error(f"Brakuje pozycji w prices.json: {error}")
    except Exception as error:
        st.error(f"Wystąpił błąd: {error}")

with cart_col:
    render_cart()

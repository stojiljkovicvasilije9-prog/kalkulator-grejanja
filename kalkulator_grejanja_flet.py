# kalkulator_grejanja_flet.py
"""
Flet port kalkulatora toplotne energije — Profesionalna verzija.

SLIKE / IKONE — kako funkcioniše:
  Aplikacija automatski traži fajlove po imenu u 2 lokacije:
    1. assets/ikonica.png   (preporučeno — podfolter 'assets' pored .py fajla)
    2. ikonica.png          (direktno pored .py fajla)
  Isto važi za ikonica.ico (desktop ikonica prozora).
  Nema hardkodovanih putanja — radi na Desktop / Android / Web.

STRUKTURA FOLDERA (preporučena):
  KalkulatorGrejanja/
  ├── kalkulator_grejanja_flet.py
  ├── requirements.txt
  ├── Dockerfile
  ├── fly.toml
  └── assets/
      ├── ikonica.png
      └── ikonica.ico
"""

import flet as ft
import threading
from math import ceil
from pathlib import Path

# ══════════════════════════════════════════════════════════════
#  PRONALAŽENJE RESURSA (slike, ikone)
# ══════════════════════════════════════════════════════════════

_BASE_DIR = Path(__file__).resolve().parent

def find_asset(filename: str) -> str | None:
    """
    Traži fajl po imenu na:
      1. <folder_aplikacije>/assets/<filename>
      2. <folder_aplikacije>/<filename>
    Vraća apsolutnu string-putanju ako postoji, None ako ne postoji.
    Aplikacija NEĆE pasti ako fajl nedostaje — samo preskače ikonicu.
    """
    for candidate in [_BASE_DIR / "assets" / filename, _BASE_DIR / filename]:
        if candidate.exists():
            return str(candidate)
    return None

# ── Resursi — samo menjaj IME FAJLA ako preimenuješ slike ────
ICON_PNG = find_asset("ikonica.png")   # PNG ikonica (splash ekran + header logo)
ICON_ICO = find_asset("ikonica.ico")   # ICO ikonica (naslov prozora, samo Desktop)
# Ako dodaješ nove slike, dodaj ih ovde istim obrascem:
# LOGO_PNG   = find_asset("logo.png")
# BANNER_PNG = find_asset("banner.png")
# ─────────────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════════════
#  BACKEND — LOGIKA (NE MENJATI FORMULE NI VARIJABLE)
# ══════════════════════════════════════════════════════════════

BASE_W_PER_M2 = 100.0

DOSTUPNE_SNAGE_KW = [6, 8, 10, 12, 15, 20, 25, 30, 40, 50]

FUEL_PRICES = {
    "Električna energija": 10.0,
    "Gas (NG/PG)": 15.0,
    "Peleti": 12.0,
    "Drvo": 8.0,
    "Ugalj": 7.0,
    "Geotermalna energija": 5.0,
    "Solarna toplota (akumulacija)": 1.0
}

WALL_MATERIAL_FACTORS = {
    "Cigla puna": 1.05,
    "Cigla šuplja": 1.0,
    "Beton": 1.25,
    "Blok (betonski blok)": 1.10,
    "Siporeks / gas-beton": 0.95,
    "Kamen": 1.2,
    "Drvena konstrukcija": 0.85,
    "Drveni skelet": 0.9,
    "Sendvič panel (izolovan)": 0.8,
    "Termo blok (izolovani blokovi)": 0.9
}

WALL_THICKNESS_FACTORS = {
    "10 cm": 1.15, "15 cm": 1.1, "20 cm": 1.05, "25 cm": 1.0,
    "30 cm": 0.95, "35 cm": 0.9, "40 cm": 0.85, "50 cm": 0.8
}

WINDOW_TYPE_FACTORS = {
    "Jednostruko staklo": 1.4,
    "Dvostruko izolovano (2x)": 1.0,
    "Troslojno izolovano (3x)": 0.85,
    "Low-E dvostruko": 0.95,
    "Trostruko Low-E": 0.8,
    "Panoramski prozor": 0.9,
    "Krovni prozor": 1.05,
    "Klizni prozor": 1.1,
    "PVC jednokrilni": 1.05,
    "PVC dvokrilni": 1.02,
    "Drveni prozor": 1.10,
    "Aluminijumski prozor": 1.15
}

ROOF_FACTORS = {
    "Ravan": 1.05, "Kosi": 1.0,
    "Potkrovlje izolovano": 0.9, "Potkrovlje neizolovano": 1.2
}

ORIENTATION_FACTORS = {
    "Sever": 1.12, "Istočna/Zapadna": 1.02, "Jug": 0.92
}

BUILDING_TYPE_FACTORS = {
    "Kuća (samostalna)": 1.05, "Stan (zgrada)": 0.95,
    "Vikendica": 1.1, "Hala / veliki prostor": 1.2
}

UNDERFLOOR_HEATING_FACTORS = {"Da": 0.9, "Ne": 1.0}

ISOLATION_MATERIAL_FACTORS = {
    "Bez izolacije": 1.0, "Kamena vuna": 0.95, "Staklena vuna": 0.96,
    "Drvena vuna": 0.97, "Stiropor (EPS)": 0.92, "Stirodur (XPS)": 0.90,
    "Grafitni stiropor": 0.88, "PUR/PIR paneli": 0.85
}

ISOLATION_THICKNESSES = ["0", "5", "10", "15"]

FLOOR_TYPES = [
    "Laminat", "Pločice", "Parket", "Beton", "Tepih",
    "Epoksid", "Vinil", "Mermer", "Granit", "Linoleum", "Brodski pod"
]


def window_percent_factor(percent):
    if percent <= 5:    return 0.95
    elif percent <= 10: return 1.0
    elif percent <= 20: return 1.1
    elif percent <= 30: return 1.25
    else:               return 1.35


def nearest_commercial_boiler(required_kw):
    for p in DOSTUPNE_SNAGE_KW:
        if p >= required_kw:
            return p
    return DOSTUPNE_SNAGE_KW[-1]


# ══════════════════════════════════════════════════════════════
#  FLET UI — BOJE I STILOVI
# ══════════════════════════════════════════════════════════════

BG_DARK    = "#121212"
BG_CARD    = "#1E1E1E"
BG_CARD2   = "#252525"
ACCENT     = "#00E676"
ACCENT2    = "#FF6B35"
TEXT_PRI   = "#FFFFFF"
TEXT_SEC   = "#B0BEC5"
TEXT_MUTED = "#607D8B"
BORDER     = "#333333"


# ══════════════════════════════════════════════════════════════
#  POMOĆNE UI FUNKCIJE
# ══════════════════════════════════════════════════════════════

def section_title(text: str) -> ft.Container:
    return ft.Container(
        content=ft.Text(text, color=ACCENT, size=13, weight=ft.FontWeight.BOLD),
        padding=ft.padding.only(left=8, top=10, bottom=4),
        border=ft.border.only(left=ft.BorderSide(3, ACCENT)),
        margin=ft.margin.only(bottom=2),
    )


def make_dropdown(label, options, value, width=220):
    chk = ft.Checkbox(value=True, fill_color=ACCENT, check_color="#000")
    dd = ft.Dropdown(
        value=value,
        options=[ft.dropdown.Option(o) for o in options],
        width=width, color=TEXT_PRI, bgcolor=BG_CARD2,
        border_color=BORDER, focused_border_color=ACCENT,
        text_size=12, content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
    )
    row = ft.Row(controls=[
        chk,
        ft.Text(label, color=TEXT_SEC, size=12, width=240),
        dd,
    ], spacing=6)
    return chk, dd, row


def make_textfield(label, default, width=110):
    chk = ft.Checkbox(value=True, fill_color=ACCENT, check_color="#000")
    tf = ft.TextField(
        value=default, width=width, color=TEXT_PRI, bgcolor=BG_CARD2,
        border_color=BORDER, focused_border_color=ACCENT,
        text_size=12, content_padding=ft.padding.symmetric(horizontal=8, vertical=6),
    )
    row = ft.Row(controls=[
        chk,
        ft.Text(label, color=TEXT_SEC, size=12, width=240),
        tf,
    ], spacing=6)
    return chk, tf, row


# ══════════════════════════════════════════════════════════════
#  GLAVNA FLET APLIKACIJA
# ══════════════════════════════════════════════════════════════

def main(page: ft.Page):
    page.title = "Kalkulator potrebne toplotne energije"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_DARK
    page.padding = 0
    page.window_width = 1440
    page.window_height = 900

    # ── Desktop ikonica prozora (ICO) ────────────────────────
    if ICON_ICO:
        page.window_icon = ICON_ICO

    # ── SPLASH EKRAN (prikazuje se samo ako postoji ikonica.png) ──
    splash_dlg = None
    if ICON_PNG:
        splash_dlg = ft.AlertDialog(
            modal=True,
            bgcolor=BG_DARK,
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Image(src=ICON_PNG, width=220, height=220, fit="contain"),
                        ft.Text("Učitavanje...", color=TEXT_SEC, size=13),
                        ft.ProgressRing(color=ACCENT, width=28, height=28, stroke_width=3),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=16,
                ),
                padding=ft.padding.all(40),
                alignment=ft.alignment.center,
            ),
            shape=ft.RoundedRectangleBorder(radius=16),
        )
        page.overlay.append(splash_dlg)
        splash_dlg.open = True
        page.update()

        def close_splash():
            if splash_dlg:
                splash_dlg.open = False
                page.update()

        threading.Timer(2.5, close_splash).start()

    # ── HEADER ───────────────────────────────────────────────
    if ICON_PNG:
        header_icon = ft.Image(src=ICON_PNG, width=32, height=32, fit="contain")
    else:
        header_icon = ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=ACCENT, size=28)

    header = ft.Container(
        content=ft.Row(controls=[
            header_icon,
            ft.Text(
                "Kalkulator potrebne toplotne energije — Profesionalna verzija",
                color=TEXT_PRI, size=17, weight=ft.FontWeight.BOLD,
            ),
        ], spacing=12),
        bgcolor="#0D0D0D",
        padding=ft.padding.symmetric(horizontal=20, vertical=13),
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
    )

    # ── OPŠTI PARAMETRI ──────────────────────────────────────
    pov_chk,  pov_tf,  pov_row  = make_textfield("Ukupna površina objekta (m²):", "50")
    vis_chk,  vis_tf,  vis_row  = make_textfield("Visina plafona (m):", "2.7")
    sprat_chk, sprat_tf, sprat_row = make_textfield("Spratnost (ručni unos):", "1")
    price_chk, price_tf, price_row = make_textfield("Cena energije (RSD/kWh):", "12")
    rad_chk,  rad_tf,  rad_row  = make_textfield("Broj radijatora u objektu:", "5")
    uf_area_chk, uf_area_tf, uf_area_row = make_textfield("Površina podnog grejanja (m²):", "0")

    btype_chk, btype_dd, btype_row = make_dropdown(
        "Vrsta objekta:", list(BUILDING_TYPE_FACTORS.keys()), "Stan (zgrada)")
    op_izol_mat_chk, op_izol_mat_dd, op_izol_mat_row = make_dropdown(
        "Opšta izolacija - materijal:", list(ISOLATION_MATERIAL_FACTORS.keys()), "Stiropor (EPS)")
    op_izol_deb_chk, op_izol_deb_dd, op_izol_deb_row = make_dropdown(
        "Opšta izolacija - debljina (cm):", ISOLATION_THICKNESSES, "10", width=110)
    un_izol_mat_chk, un_izol_mat_dd, un_izol_mat_row = make_dropdown(
        "Unutrašnja izolacija - materijal:", list(ISOLATION_MATERIAL_FACTORS.keys()), "Bez izolacije")
    un_izol_deb_chk, un_izol_deb_dd, un_izol_deb_row = make_dropdown(
        "Unutrašnja izolacija - debljina (cm):", ISOLATION_THICKNESSES, "5", width=110)
    matz_chk, matz_dd, matz_row = make_dropdown(
        "Materijal zidova:", list(WALL_MATERIAL_FACTORS.keys()), "Cigla šuplja")
    th_chk, th_dd, th_row = make_dropdown(
        "Debljina zidova:", list(WALL_THICKNESS_FACTORS.keys()), "30 cm", width=140)
    orient_chk, orient_dd, orient_row = make_dropdown(
        "Orijentacija:", list(ORIENTATION_FACTORS.keys()), "Istočna/Zapadna", width=170)
    uf_chk, uf_dd, uf_row = make_dropdown(
        "Podno grejanje (globalno):", ["Ne", "Da"], "Ne", width=100)
    ceil_izol_mat_chk, ceil_izol_mat_dd, ceil_izol_mat_row = make_dropdown(
        "Izolacija plafona - materijal:", list(ISOLATION_MATERIAL_FACTORS.keys()), "Bez izolacije")
    ceil_izol_deb_chk, ceil_izol_deb_dd, ceil_izol_deb_row = make_dropdown(
        "Izolacija plafona - debljina (cm):", ISOLATION_THICKNESSES, "0", width=110)
    roof_chk, roof_dd, roof_row = make_dropdown(
        "Tip krova/plafona:", list(ROOF_FACTORS.keys()), "Ravan", width=180)

    # ── SOBE ─────────────────────────────────────────────────
    rooms_count_chk = ft.Checkbox(value=True, fill_color=ACCENT, check_color="#000")
    rooms_count_tf = ft.TextField(
        value="3", width=70, color=TEXT_PRI, bgcolor=BG_CARD2,
        border_color=BORDER, focused_border_color=ACCENT, text_size=12,
        content_padding=ft.padding.symmetric(horizontal=8, vertical=6),
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    rooms_column = ft.Column(spacing=10)
    room_blocks = []

    def make_room_block(index: int) -> dict:
        room_chk = ft.Checkbox(
            value=True, fill_color=ACCENT, check_color="#000",
            label=f"Soba {index}",
            label_style=ft.TextStyle(color=ACCENT, weight=ft.FontWeight.BOLD, size=13),
        )
        area_tf = ft.TextField(
            value="12", width=100, label="Površina (m²)", color=TEXT_PRI,
            bgcolor=BG_CARD2, border_color=BORDER, focused_border_color=ACCENT, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=6),
        )
        window_area_tf = ft.TextField(
            value="1.5", width=100, label="Prozori (m²)", color=TEXT_PRI,
            bgcolor=BG_CARD2, border_color=BORDER, focused_border_color=ACCENT, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=6),
        )
        window_type_dd = ft.Dropdown(
            value=list(WINDOW_TYPE_FACTORS.keys())[1],
            options=[ft.dropdown.Option(o) for o in WINDOW_TYPE_FACTORS.keys()],
            label="Vrsta prozora", width=210, color=TEXT_PRI, bgcolor=BG_CARD2,
            border_color=BORDER, focused_border_color=ACCENT, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
        )
        floor_dd = ft.Dropdown(
            value=FLOOR_TYPES[0],
            options=[ft.dropdown.Option(o) for o in FLOOR_TYPES],
            label="Vrsta poda", width=160, color=TEXT_PRI, bgcolor=BG_CARD2,
            border_color=BORDER, focused_border_color=ACCENT, text_size=12,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
        )
        card = ft.Card(
            content=ft.Container(
                content=ft.Column(controls=[
                    ft.Row(controls=[room_chk]),
                    ft.Row(controls=[area_tf, window_area_tf, window_type_dd, floor_dd],
                           spacing=10, wrap=True),
                ], spacing=8),
                padding=12, bgcolor=BG_CARD,
            ),
            elevation=2, color=BG_CARD,
        )
        return {
            'widget': card, 'enabled': room_chk,
            'area': area_tf, 'window_area': window_area_tf,
            'window_type': window_type_dd, 'floor_type': floor_dd,
        }

    def regenerate_rooms(n: int):
        room_blocks.clear()
        rooms_column.controls.clear()
        for i in range(1, n + 1):
            rb = make_room_block(i)
            room_blocks.append(rb)
            rooms_column.controls.append(rb['widget'])
        page.update()

    def on_rooms_change(e):
        try:
            n = int(rooms_count_tf.value)
            if n >= 1:
                regenerate_rooms(n)
        except Exception:
            pass

    rooms_count_tf.on_change = on_rooms_change
    regenerate_rooms(3)

    # ── GORIVA ───────────────────────────────────────────────
    fuel_checkboxes: dict[str, ft.Checkbox] = {}
    fuel_chk_controls = []
    for fuel in FUEL_PRICES:
        chk = ft.Checkbox(
            label=fuel, value=True, fill_color=ACCENT, check_color="#000",
            label_style=ft.TextStyle(color=TEXT_SEC, size=12),
        )
        fuel_checkboxes[fuel] = chk
        fuel_chk_controls.append(chk)

    # ── REZULTATI ────────────────────────────────────────────
    result_rows = ft.Column(spacing=0)
    summary_tf = ft.TextField(
        multiline=True, min_lines=14, read_only=True, value="",
        color=TEXT_SEC, bgcolor=BG_CARD2, border_color=BORDER, text_size=12, expand=True,
    )
    error_text = ft.Text("", color="#FF5252", size=12, visible=False)

    def show_error(msg):
        error_text.value = msg
        error_text.visible = True
        page.update()

    def result_header_row():
        s = ft.TextStyle(color=ACCENT, weight=ft.FontWeight.BOLD, size=11)
        return ft.Container(
            content=ft.Row(controls=[
                ft.Text("Gorivo",               style=s, width=170),
                ft.Text("Potrebna snaga (kW)",  style=s, width=130),
                ft.Text("Prepor. kotao (kW)",   style=s, width=120),
                ft.Text("Mesečna potr. (kWh)",  style=s, width=130),
                ft.Text("Mesečni trošak (RSD)", style=s, width=140),
            ], spacing=0),
            bgcolor="#1A1A1A",
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            border=ft.border.only(bottom=ft.BorderSide(1, ACCENT)),
        )

    def make_result_row(fuel, req_kw, kotao, mes_kwh, mes_rsd, odd):
        bg = "#1E1E1E" if odd else "#252525"
        return ft.Container(
            content=ft.Row(controls=[
                ft.Text(fuel,              color=TEXT_PRI,  size=12, width=170),
                ft.Text(f"{req_kw:.2f}",  color=ACCENT,    size=12, width=130, weight=ft.FontWeight.BOLD),
                ft.Text(f"{kotao}",        color="#FFD740", size=12, width=120),
                ft.Text(f"{mes_kwh:.1f}", color=TEXT_SEC,  size=12, width=130),
                ft.Text(f"{mes_rsd:.0f}", color="#69F0AE", size=12, width=140),
            ], spacing=0),
            bgcolor=bg,
            padding=ft.padding.symmetric(horizontal=12, vertical=7),
            border=ft.border.only(bottom=ft.BorderSide(1, "#2A2A2A")),
        )

    # ── IZRAČUNAJ ────────────────────────────────────────────
    def izracunaj(e):
        error_text.visible = False
        result_rows.controls.clear()
        summary_tf.value = ""

        try:
            ukupna_pov = float(pov_tf.value) if pov_chk.value else None
        except Exception:
            show_error("Neispravna vrednost za ukupnu površinu objekta.")
            return
        try:
            visina = float(vis_tf.value) if vis_chk.value else 2.7
        except Exception:
            visina = 2.7

        factor_global = 1.0
        if op_izol_mat_chk.value:
            factor_global *= ISOLATION_MATERIAL_FACTORS.get(op_izol_mat_dd.value, 1.0)
        if un_izol_mat_chk.value:
            factor_global *= ISOLATION_MATERIAL_FACTORS.get(un_izol_mat_dd.value, 1.0)
        if matz_chk.value:
            factor_global *= WALL_MATERIAL_FACTORS.get(matz_dd.value, 1.0)
        if th_chk.value:
            factor_global *= WALL_THICKNESS_FACTORS.get(th_dd.value, 1.0)
        if orient_chk.value:
            factor_global *= ORIENTATION_FACTORS.get(orient_dd.value, 1.0)
        if btype_chk.value:
            factor_global *= BUILDING_TYPE_FACTORS.get(btype_dd.value, 1.0)
        if roof_chk.value:
            factor_global *= ROOF_FACTORS.get(roof_dd.value, 1.0)

        try:
            total_radiators = int(rad_tf.value) if rad_chk.value else 0
        except Exception:
            total_radiators = 0

        total_w = 0.0
        rooms_details = []

        if rooms_count_chk.value:
            for idx, rb in enumerate(room_blocks, start=1):
                if not rb['enabled'].value:
                    continue
                try:
                    area = float(rb['area'].value) if rb['area'].value.strip() else 0.0
                except Exception:
                    show_error(f"Greška u površini za Soba {idx}.")
                    return
                try:
                    window_area = float(rb['window_area'].value) if rb['window_area'].value.strip() else 0.0
                except Exception:
                    show_error(f"Greška u površini prozora za Soba {idx}.")
                    return

                percent = (window_area / area * 100.0) if area > 0 else 0.0
                wfactor = window_percent_factor(percent)
                wglass_factor = WINDOW_TYPE_FACTORS.get(rb['window_type'].value, 1.0)
                uf_factor = UNDERFLOOR_HEATING_FACTORS.get(uf_dd.value, 1.0) if uf_chk.value else 1.0
                ceiling_iso_factor = ISOLATION_MATERIAL_FACTORS.get(ceil_izol_mat_dd.value, 1.0) if ceil_izol_mat_chk.value else 1.0

                room_factor = wfactor * wglass_factor * uf_factor * ceiling_iso_factor
                room_base_w = BASE_W_PER_M2 * area * (visina / 2.7)
                room_required_w = room_base_w * room_factor * factor_global

                total_w += room_required_w
                rooms_details.append({
                    'index': idx, 'area': area,
                    'window_area': window_area, 'window_percent': percent,
                    'window_type': rb['window_type'].value,
                    'floor_type': rb['floor_type'].value,
                    'room_required_w': room_required_w
                })

        if not rooms_details:
            show_error("Nema uključenih soba za proračun. Proveri da li su sobe štiklirane.")
            return

        ukupni_kw_exact = total_w / 1000.0
        ukupni_kw_display = ceil(ukupni_kw_exact * 100) / 100.0

        cena_input = None
        if price_chk.value:
            try:
                cena_input = float(price_tf.value)
            except Exception:
                cena_input = None

        result_rows.controls.append(result_header_row())
        for i, (fuel, price_default) in enumerate(FUEL_PRICES.items()):
            if not fuel_checkboxes[fuel].value:
                continue
            if fuel == "Električna energija":             eff = 1.0
            elif fuel == "Gas (NG/PG)":                   eff = 0.95
            elif fuel == "Peleti":                        eff = 0.9
            elif fuel == "Drvo":                          eff = 0.85
            elif fuel == "Ugalj":                         eff = 0.9
            elif fuel == "Geotermalna energija":          eff = 0.7
            elif fuel == "Solarna toplota (akumulacija)": eff = 0.6
            else:                                         eff = 1.0

            required_kw = ukupni_kw_exact * eff
            required_kw_display = ceil(required_kw * 100) / 100.0
            predlog_kotla = nearest_commercial_boiler(required_kw_display)
            mesecna_kwh = required_kw_display * 24.0 * 30.0
            cena_kwh = cena_input if cena_input is not None else price_default
            mesecni_trosak = mesecna_kwh * cena_kwh

            result_rows.controls.append(
                make_result_row(fuel, required_kw_display, predlog_kotla, mesecna_kwh, mesecni_trosak, i % 2 == 0)
            )

        lines = []
        lines.append(f"UKUPNO: Potrebna toplotna snaga: {ukupni_kw_display:.2f} kW (precizno: {ukupni_kw_exact:.3f} kW)\n")
        lines.append(f"Ukupan broj radijatora (globalno): {total_radiators}\n")
        if ukupna_pov is not None:
            lines.append(f"Zadata ukupna površina objekta: {ukupna_pov} m²\n")
        lines.append("\n--- Detalji po sobama ---\n")
        for rd in rooms_details:
            lines.append(f"Soba {rd['index']}: P={rd['area']} m², Prozori={rd['window_area']} m² "
                         f"({rd['window_percent']:.1f}%), Tip prozora={rd['window_type']}, Pod={rd['floor_type']}\n")
            lines.append(f"  Procena: {rd['room_required_w']:.0f} W ({rd['room_required_w']/1000.0:.2f} kW)\n\n")
        lines.append("\n--- Korišćeni GLOBALNI faktori ---\n")
        if op_izol_mat_chk.value:
            lines.append(f"Opšta izolacija: {op_izol_mat_dd.value} — {op_izol_deb_dd.value} cm\n")
        if un_izol_mat_chk.value:
            lines.append(f"Unutrašnja izolacija: {un_izol_mat_dd.value} — {un_izol_deb_dd.value} cm\n")
        if matz_chk.value:
            lines.append(f"Materijal zidova: {matz_dd.value}\n")
        if th_chk.value:
            lines.append(f"Debljina zidova: {th_dd.value}\n")
        if orient_chk.value:
            lines.append(f"Orijentacija: {orient_dd.value}\n")
        if btype_chk.value:
            lines.append(f"Vrsta objekta: {btype_dd.value}\n")
        if roof_chk.value:
            lines.append(f"Tip krova: {roof_dd.value}\n")
        if uf_chk.value:
            lines.append(f"Podno grejanje: {uf_dd.value} — površina: {uf_area_tf.value} m²\n")
        if ceil_izol_mat_chk.value:
            lines.append(f"Izolacija plafona: {ceil_izol_mat_dd.value} — {ceil_izol_deb_dd.value} cm\n")
        lines.append("\n--- Procene po gorivu su prikazane u tabeli iznad ---\n")

        summary_tf.value = "".join(lines)
        page.update()

    # ── LAYOUT ───────────────────────────────────────────────
    left_card = ft.Card(
        content=ft.Container(
            content=ft.Column(controls=[
                section_title("OPŠTI PODACI"),
                pov_row, vis_row,
                ft.Row(controls=[
                    rooms_count_chk,
                    ft.Text("Broj soba:", color=TEXT_SEC, size=12, width=240),
                    rooms_count_tf,
                ], spacing=6),
                sprat_row, btype_row,
                ft.Divider(color=BORDER, height=10),
                section_title("IZOLACIJA"),
                op_izol_mat_row, op_izol_deb_row,
                un_izol_mat_row, un_izol_deb_row,
                ft.Divider(color=BORDER, height=10),
                section_title("ZIDOVI I KONSTRUKCIJA"),
                matz_row, th_row, orient_row,
                ft.Divider(color=BORDER, height=10),
                section_title("OSTALO"),
                price_row, rad_row, uf_row, uf_area_row,
                ceil_izol_mat_row, ceil_izol_deb_row, roof_row,
                ft.Text("Odznačen checkbox = parametar se ne uračunava.",
                        color=TEXT_MUTED, size=10, italic=True),
            ], spacing=4, scroll=ft.ScrollMode.AUTO),
            padding=16, bgcolor=BG_CARD,
        ),
        elevation=4, color=BG_CARD,
    )

    rooms_card = ft.Card(
        content=ft.Container(
            content=ft.Column(controls=[
                section_title("SOBE"),
                rooms_column,
            ], spacing=8, scroll=ft.ScrollMode.AUTO),
            padding=16, bgcolor=BG_CARD,
        ),
        elevation=4, color=BG_CARD,
    )

    fuels_card = ft.Card(
        content=ft.Container(
            content=ft.Column(controls=[
                section_title("GORIVA"),
                ft.Column(controls=fuel_chk_controls, spacing=2),
            ], spacing=6),
            padding=16, bgcolor=BG_CARD,
        ),
        elevation=4, color=BG_CARD,
    )

    calc_btn = ft.Container(
        content=ft.ElevatedButton(
            text="IZRAČUNAJ",
            icon=ft.Icons.CALCULATE,
            on_click=izracunaj,
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ACCENT2, ft.ControlState.HOVERED: "#FF8C60"},
                color={ft.ControlState.DEFAULT: "#FFFFFF"},
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=32, vertical=16),
                text_style=ft.TextStyle(size=15, weight=ft.FontWeight.BOLD),
            ),
            width=200, height=52,
        ),
        alignment=ft.alignment.center,
        padding=ft.padding.symmetric(vertical=8),
    )

    results_card = ft.Card(
        content=ft.Container(
            content=ft.Column(controls=[
                section_title("REZULTATI PRORAČUNA"),
                error_text,
                ft.Container(
                    content=result_rows,
                    bgcolor=BG_CARD2,
                    border_radius=8,
                    border=ft.border.all(1, BORDER),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                ft.Divider(color=BORDER, height=10),
                section_title("TEKSTUALNI REZIME"),
                summary_tf,
            ], spacing=8, expand=True),
            padding=16, bgcolor=BG_CARD, expand=True,
        ),
        elevation=4, color=BG_CARD, expand=True,
    )

    body = ft.Container(
        content=ft.Row(controls=[
            ft.Container(
                content=ft.Column(controls=[left_card, rooms_card],
                                  spacing=10, scroll=ft.ScrollMode.AUTO, expand=True),
                expand=5,
            ),
            ft.VerticalDivider(width=1, color=BORDER),
            ft.Container(
                content=ft.Column(controls=[fuels_card, calc_btn, results_card],
                                  spacing=10, scroll=ft.ScrollMode.AUTO, expand=True),
                expand=4,
            ),
        ], expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
        expand=True,
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
    )

    page.add(ft.Column(controls=[header, body], spacing=0, expand=True))
    page.update()


# ══════════════════════════════════════════════════════════════
#  POKRETANJE — WEB MOD (za Fly.io deploy)
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        port=8080,
        host="0.0.0.0",
    )

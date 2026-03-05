# kalkulator_grejanja_flet.py
"""
Kalkulator potrebne toplotne energije — Profesionalna verzija
Autor: Vasilije Stojiljković, ETS Nikola Tesla, Niš
"""

import flet as ft
import threading
from math import ceil
from pathlib import Path

# ══════════════════════════════════════════════════════════════
#  PRONALAŽENJE RESURSA
# ══════════════════════════════════════════════════════════════

_BASE_DIR = Path(__file__).resolve().parent

def find_asset(filename: str) -> str | None:
    for candidate in [_BASE_DIR / "assets" / filename, _BASE_DIR / filename]:
        if candidate.exists():
            return str(candidate)
    return None

ICON_PNG = find_asset("ikonica.png")
ICON_ICO = find_asset("ikonica.ico")


# ══════════════════════════════════════════════════════════════
#  BACKEND — KOMPLETNA LOGIKA PRORAČUNA
# ══════════════════════════════════════════════════════════════

BASE_W_PER_M2 = 100.0
DELTA_T       = 35.0
SAFETY_FACTOR = 1.15
HEATING_HOURS = 1800

DOSTUPNE_SNAGE_KW = [6, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100]

FUEL_PRICES = {
    "Električna energija":          10.0,
    "Gas (NG/PG)":                  15.0,
    "Peleti":                       12.0,
    "Drvo":                          8.0,
    "Ugalj":                         7.0,
    "Geotermalna energija":          5.0,
    "Solarna toplota (akumulacija)": 1.0,
}

FUEL_EFFICIENCY = {
    "Električna energija":           1.00,
    "Gas (NG/PG)":                   0.92,
    "Peleti":                        0.88,
    "Drvo":                          0.80,
    "Ugalj":                         0.82,
    "Geotermalna energija":          3.50,
    "Solarna toplota (akumulacija)": 0.55,
}

WALL_MATERIAL_FACTORS = {
    "Cigla puna":                     1.05,
    "Cigla šuplja":                   1.00,
    "Beton":                          1.25,
    "Blok (betonski blok)":           1.10,
    "Siporeks / gas-beton":           0.95,
    "Kamen":                          1.20,
    "Drvena konstrukcija":            0.85,
    "Drveni skelet":                  0.90,
    "Sendvič panel (izolovan)":       0.80,
    "Termo blok (izolovani blokovi)": 0.90,
}

WALL_THICKNESS_FACTORS = {
    "10 cm": 1.15, "15 cm": 1.10, "20 cm": 1.05,
    "25 cm": 1.00, "30 cm": 0.95, "35 cm": 0.90,
    "40 cm": 0.85, "50 cm": 0.80,
}

WINDOW_TYPE_FACTORS = {
    "Jednostruko staklo":        1.40,
    "Dvostruko izolovano (2x)":  1.00,
    "Troslojno izolovano (3x)":  0.85,
    "Low-E dvostruko":           0.95,
    "Trostruko Low-E":           0.80,
    "Panoramski prozor":         0.90,
    "Krovni prozor":             1.05,
    "Klizni prozor":             1.10,
    "PVC jednokrilni":           1.05,
    "PVC dvokrilni":             1.02,
    "Drveni prozor":             1.10,
    "Aluminijumski prozor":      1.15,
}

ROOF_FACTORS = {
    "Ravan":                  1.05,
    "Kosi":                   1.00,
    "Potkrovlje izolovano":   0.90,
    "Potkrovlje neizolovano": 1.20,
}

ORIENTATION_FACTORS = {
    "Sever":           1.12,
    "Istočna/Zapadna": 1.02,
    "Jug":             0.92,
}

BUILDING_TYPE_FACTORS = {
    "Kuća (samostalna)":     1.05,
    "Stan (zgrada)":         0.95,
    "Vikendica":             1.10,
    "Hala / veliki prostor": 1.20,
}

UNDERFLOOR_HEATING_FACTORS = {
    "Ne":                             1.00,
    "Da — vodeno podno grejanje":     0.88,
    "Da — električno podno grejanje": 0.93,
}

ISOLATION_MATERIAL_FACTORS = {
    "Bez izolacije":     1.00,
    "Kamena vuna":       0.95,
    "Staklena vuna":     0.96,
    "Drvena vuna":       0.97,
    "Stiropor (EPS)":    0.92,
    "Stirodur (XPS)":    0.90,
    "Grafitni stiropor": 0.88,
    "PUR/PIR paneli":    0.85,
}

ISOLATION_THICKNESS_FACTORS = {
    "0":  1.00, "5":  0.97, "8":  0.95,
    "10": 0.93, "12": 0.91, "15": 0.88, "20": 0.84,
}

ISOLATION_THICKNESSES = ["0", "5", "8", "10", "12", "15", "20"]

FLOOR_COUNT_FACTORS = {
    "P (prizemlje)": 1.15,
    "P+1":           1.00,
    "P+2":           0.95,
    "P+3 i više":    0.90,
}

FLOOR_TYPES = [
    "Laminat", "Pločice", "Parket", "Beton", "Tepih",
    "Epoksid", "Vinil", "Mermer", "Granit", "Linoleum", "Brodski pod",
]


def window_percent_factor(percent):
    if percent <= 5:    return 0.95
    elif percent <= 10: return 1.00
    elif percent <= 20: return 1.10
    elif percent <= 30: return 1.25
    else:               return 1.35


def nearest_commercial_boiler(required_kw):
    for p in DOSTUPNE_SNAGE_KW:
        if p >= required_kw:
            return p
    return DOSTUPNE_SNAGE_KW[-1]


# ══════════════════════════════════════════════════════════════
#  BOJE
# ══════════════════════════════════════════════════════════════

BG_DARK    = "#0F0F0F"
BG_CARD    = "#1A1A1A"
BG_CARD2   = "#222222"
BG_CARD3   = "#2A2A2A"
GREEN      = "#00C853"
RED        = "#FF1744"
ACCENT     = "#00E676"
ACCENT2    = "#FF6B35"
YELLOW     = "#FFD600"
TEXT_PRI   = "#FFFFFF"
TEXT_SEC   = "#B0BEC5"
TEXT_MUTED = "#546E7A"
BORDER     = "#2E2E2E"


# ══════════════════════════════════════════════════════════════
#  POMOĆNE UI FUNKCIJE
# ══════════════════════════════════════════════════════════════

def section_title(text):
    return ft.Container(
        content=ft.Text(text, color=ACCENT, size=12, weight=ft.FontWeight.BOLD),
        padding=ft.padding.only(left=8, top=8, bottom=3),
        border=ft.border.only(left=ft.BorderSide(3, ACCENT)),
        margin=ft.margin.only(bottom=2),
    )


def make_chk(value=True):
    c = ft.Checkbox(value=value, fill_color=GREEN if value else RED, check_color="#000")
    def on_change(e):
        c.fill_color = GREEN if c.value else RED
        c.update()
    c.on_change = on_change
    return c


def make_dropdown(label, options, value, width=210):
    chk = make_chk(True)
    dd = ft.Dropdown(
        value=value,
        options=[ft.dropdown.Option(o) for o in options],
        width=width, color=TEXT_PRI, bgcolor=BG_CARD2,
        border_color=BORDER, focused_border_color=ACCENT,
        text_size=11, content_padding=ft.padding.symmetric(horizontal=8, vertical=3),
    )
    row = ft.Row(controls=[chk, ft.Text(label, color=TEXT_SEC, size=11, width=230), dd], spacing=5)
    return chk, dd, row


def make_textfield(label, default, width=100):
    chk = make_chk(True)
    tf = ft.TextField(
        value=default, width=width, color=TEXT_PRI, bgcolor=BG_CARD2,
        border_color=BORDER, focused_border_color=ACCENT,
        text_size=11, content_padding=ft.padding.symmetric(horizontal=8, vertical=5),
    )
    row = ft.Row(controls=[chk, ft.Text(label, color=TEXT_SEC, size=11, width=230), tf], spacing=5)
    return chk, tf, row


# ══════════════════════════════════════════════════════════════
#  GLAVNA APLIKACIJA
# ══════════════════════════════════════════════════════════════

def main(page: ft.Page):
    page.title = "Kalkulator toplotne energije — V. Stojiljković"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_DARK
    page.padding = 0
    page.window_width = 1500
    page.window_height = 920

    if ICON_ICO:
        page.window_icon = ICON_ICO

    # ── SPLASH ───────────────────────────────────────────────
    splash_controls = [
        ft.Text("Kalkulator toplotne energije", color=ACCENT, size=18, weight=ft.FontWeight.BOLD),
        ft.Text("Učitavanje...", color=TEXT_SEC, size=12),
        ft.ProgressRing(color=ACCENT, width=30, height=30, stroke_width=3),
        ft.Text("Vasilije Stojiljković | ETS Nikola Tesla, Niš", color=TEXT_MUTED, size=10),
    ]
    if ICON_PNG:
        splash_controls.insert(0, ft.Image(src=ICON_PNG, width=160, height=160))

    splash_dlg = ft.AlertDialog(
        modal=True, bgcolor=BG_DARK,
        content=ft.Container(
            content=ft.Column(
                controls=splash_controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            ),
            padding=ft.padding.all(40),
        ),
        shape=ft.RoundedRectangleBorder(radius=16),
    )
    page.overlay.append(splash_dlg)
    splash_dlg.open = True
    page.update()
    threading.Timer(2.5, lambda: [setattr(splash_dlg, 'open', False), page.update()]).start()

    # ── HEADER ───────────────────────────────────────────────
    if ICON_PNG:
        hdr_icon = ft.Image(src=ICON_PNG, width=34, height=34)
    else:
        hdr_icon = ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=ACCENT, size=28)

    header = ft.Container(
        content=ft.Row(controls=[
            hdr_icon,
            ft.Column(controls=[
                ft.Text("Kalkulator potrebne toplotne energije",
                        color=TEXT_PRI, size=15, weight=ft.FontWeight.BOLD),
                ft.Text("Profesionalna verzija", color=TEXT_SEC, size=10),
            ], spacing=1),
            ft.Container(expand=True),
            ft.Column(controls=[
                ft.Text("Autor: Vasilije Stojiljković", color=ACCENT, size=11, weight=ft.FontWeight.BOLD),
                ft.Text("ETS Nikola Tesla, Niš", color=TEXT_SEC, size=10),
            ], spacing=1, horizontal_alignment=ft.CrossAxisAlignment.END),
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor="#080808",
        padding=ft.padding.symmetric(horizontal=20, vertical=11),
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
    )

    # ── OPŠTI PARAMETRI ──────────────────────────────────────
    pov_chk,  pov_tf,  pov_row  = make_textfield("Ukupna površina objekta (m²):", "80")
    vis_chk,  vis_tf,  vis_row  = make_textfield("Visina plafona (m):", "2.7")
    sprat_chk, sprat_tf, sprat_row = make_textfield("Spratnost (ručni unos):", "1")
    price_chk, price_tf, price_row = make_textfield("Cena energije (RSD/kWh):", "12")
    rad_chk,  rad_tf,  rad_row  = make_textfield("Broj radijatora u objektu:", "8")
    uf_area_chk, uf_area_tf, uf_area_row = make_textfield("Površina podnog grejanja (m²):", "0")

    btype_chk,  btype_dd,  btype_row  = make_dropdown("Vrsta objekta:", list(BUILDING_TYPE_FACTORS.keys()), "Stan (zgrada)")
    floors_chk, floors_dd, floors_row = make_dropdown("Spratnost:", list(FLOOR_COUNT_FACTORS.keys()), "P+1", width=140)
    matz_chk,   matz_dd,   matz_row   = make_dropdown("Materijal zidova:", list(WALL_MATERIAL_FACTORS.keys()), "Cigla šuplja")
    th_chk,     th_dd,     th_row     = make_dropdown("Debljina zidova:", list(WALL_THICKNESS_FACTORS.keys()), "25 cm", width=110)
    orient_chk, orient_dd, orient_row = make_dropdown("Orijentacija:", list(ORIENTATION_FACTORS.keys()), "Istočna/Zapadna", width=160)
    roof_chk,   roof_dd,   roof_row   = make_dropdown("Tip krova/plafona:", list(ROOF_FACTORS.keys()), "Ravan", width=180)
    uf_chk,     uf_dd,     uf_row     = make_dropdown("Podno grejanje:", list(UNDERFLOOR_HEATING_FACTORS.keys()), "Ne", width=240)

    op_izol_mat_chk,   op_izol_mat_dd,   op_izol_mat_row   = make_dropdown("Opšta izolacija - materijal:", list(ISOLATION_MATERIAL_FACTORS.keys()), "Stiropor (EPS)")
    op_izol_deb_chk,   op_izol_deb_dd,   op_izol_deb_row   = make_dropdown("Opšta izolacija - debljina (cm):", ISOLATION_THICKNESSES, "10", width=80)
    un_izol_mat_chk,   un_izol_mat_dd,   un_izol_mat_row   = make_dropdown("Unutrašnja izolacija - materijal:", list(ISOLATION_MATERIAL_FACTORS.keys()), "Bez izolacije")
    un_izol_deb_chk,   un_izol_deb_dd,   un_izol_deb_row   = make_dropdown("Unutrašnja izolacija - debljina (cm):", ISOLATION_THICKNESSES, "0", width=80)
    ceil_izol_mat_chk, ceil_izol_mat_dd, ceil_izol_mat_row = make_dropdown("Izolacija plafona - materijal:", list(ISOLATION_MATERIAL_FACTORS.keys()), "Bez izolacije")
    ceil_izol_deb_chk, ceil_izol_deb_dd, ceil_izol_deb_row = make_dropdown("Izolacija plafona - debljina (cm):", ISOLATION_THICKNESSES, "0", width=80)

    # ── SOBE ─────────────────────────────────────────────────
    rooms_count_chk = make_chk(True)
    rooms_count_tf = ft.TextField(
        value="3", width=60, color=TEXT_PRI, bgcolor=BG_CARD2,
        border_color=BORDER, focused_border_color=ACCENT, text_size=11,
        content_padding=ft.padding.symmetric(horizontal=8, vertical=5),
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    rooms_column = ft.Column(spacing=8)
    room_blocks = []

    def auto_distribute_area():
        try:
            if not pov_chk.value:
                return
            total = float(pov_tf.value or 0)
            active = [rb for rb in room_blocks if rb['enabled'].value]
            n = len(active)
            if n > 0 and total > 0:
                per_room = round(total / n, 1)
                for rb in active:
                    rb['area'].value = str(per_room)
                    rb['area'].update()
        except Exception:
            pass

    def make_room_block(index):
        room_chk = make_chk(True)
        room_label = ft.Text(f"Soba {index}", color=ACCENT, weight=ft.FontWeight.BOLD, size=12)
        room_result = ft.Text("", color=YELLOW, size=11, weight=ft.FontWeight.BOLD)

        area_tf = ft.TextField(
            value="20", width=95, label="Površina (m²)", color=TEXT_PRI,
            bgcolor=BG_CARD3, border_color=BORDER, focused_border_color=ACCENT,
            text_size=11, content_padding=ft.padding.symmetric(horizontal=8, vertical=5),
        )
        window_area_tf = ft.TextField(
            value="1.5", width=95, label="Prozori (m²)", color=TEXT_PRI,
            bgcolor=BG_CARD3, border_color=BORDER, focused_border_color=ACCENT,
            text_size=11, content_padding=ft.padding.symmetric(horizontal=8, vertical=5),
        )
        window_type_dd = ft.Dropdown(
            value=list(WINDOW_TYPE_FACTORS.keys())[1],
            options=[ft.dropdown.Option(o) for o in WINDOW_TYPE_FACTORS.keys()],
            label="Vrsta prozora", width=200, color=TEXT_PRI, bgcolor=BG_CARD3,
            border_color=BORDER, focused_border_color=ACCENT, text_size=11,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=3),
        )
        floor_dd = ft.Dropdown(
            value=FLOOR_TYPES[0],
            options=[ft.dropdown.Option(o) for o in FLOOR_TYPES],
            label="Vrsta poda", width=155, color=TEXT_PRI, bgcolor=BG_CARD3,
            border_color=BORDER, focused_border_color=ACCENT, text_size=11,
            content_padding=ft.padding.symmetric(horizontal=8, vertical=3),
        )

        room_card = ft.Card(
            content=ft.Container(
                content=ft.Column(controls=[
                    ft.Row(controls=[room_chk, room_label, ft.Container(expand=True), room_result]),
                    ft.Row(controls=[area_tf, window_area_tf, window_type_dd, floor_dd], spacing=8, wrap=True),
                ], spacing=6),
                padding=10, bgcolor=BG_CARD2,
            ),
            elevation=1,
        )
        return {
            'widget': room_card, 'enabled': room_chk, 'index': index,
            'area': area_tf, 'window_area': window_area_tf,
            'window_type': window_type_dd, 'floor_type': floor_dd,
            'result_text': room_result,
        }

    def regenerate_rooms(n):
        room_blocks.clear()
        rooms_column.controls.clear()
        for i in range(1, n + 1):
            rb = make_room_block(i)
            room_blocks.append(rb)
            rooms_column.controls.append(rb['widget'])
        auto_distribute_area()
        page.update()

    def on_rooms_change(e):
        try:
            n = int(rooms_count_tf.value)
            if 1 <= n <= 50:
                regenerate_rooms(n)
        except Exception:
            pass

    rooms_count_tf.on_change = on_rooms_change
    pov_tf.on_change = lambda e: auto_distribute_area()
    regenerate_rooms(3)

    # ── GORIVA ───────────────────────────────────────────────
    fuel_checkboxes = {}
    fuel_chk_controls = []
    for fuel in FUEL_PRICES:
        chk = make_chk(True)
        fuel_checkboxes[fuel] = chk
        fuel_chk_controls.append(ft.Row(controls=[chk, ft.Text(fuel, color=TEXT_SEC, size=11)], spacing=6))

    # ── REZULTATI ────────────────────────────────────────────
    result_rows = ft.Column(spacing=0)
    summary_tf = ft.TextField(
        multiline=True, min_lines=16, read_only=True, value="",
        color=TEXT_SEC, bgcolor=BG_CARD2, border_color=BORDER, text_size=11, expand=True,
    )
    error_text = ft.Text("", color=RED, size=12, visible=False, weight=ft.FontWeight.BOLD)
    total_power_text = ft.Text("—", color=ACCENT, size=26, weight=ft.FontWeight.BOLD)
    boiler_text      = ft.Text("—", color=YELLOW, size=13)
    safety_text      = ft.Text("", color=TEXT_MUTED, size=10)

    power_card = ft.Card(
        content=ft.Container(
            content=ft.Column(controls=[
                ft.Text("UKUPNA POTREBNA SNAGA GREJANJA", color=TEXT_SEC, size=10, weight=ft.FontWeight.BOLD),
                total_power_text, boiler_text, safety_text,
            ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=14, bgcolor=BG_CARD,
        ),
        elevation=3,
    )

    def result_header_row():
        s = ft.TextStyle(color=ACCENT, weight=ft.FontWeight.BOLD, size=10)
        return ft.Container(
            content=ft.Row(controls=[
                ft.Text("Gorivo",       style=s, width=155),
                ft.Text("Snaga (kW)",   style=s, width=80),
                ft.Text("Kotao (kW)",   style=s, width=80),
                ft.Text("Mes. kWh",     style=s, width=80),
                ft.Text("Mes. RSD",     style=s, width=90),
                ft.Text("God. RSD",     style=s, width=90),
            ], spacing=0),
            bgcolor="#111",
            padding=ft.padding.symmetric(horizontal=10, vertical=7),
            border=ft.border.only(bottom=ft.BorderSide(1, ACCENT)),
        )

    def make_result_row(fuel, req_kw, kotao, mes_kwh, mes_rsd, god_rsd, odd):
        bg = BG_CARD if odd else BG_CARD2
        return ft.Container(
            content=ft.Row(controls=[
                ft.Text(fuel,              color=TEXT_PRI,  size=11, width=155),
                ft.Text(f"{req_kw:.2f}",  color=ACCENT,    size=11, width=80, weight=ft.FontWeight.BOLD),
                ft.Text(f"{kotao} kW",    color=YELLOW,    size=11, width=80),
                ft.Text(f"{mes_kwh:.0f}", color=TEXT_SEC,  size=11, width=80),
                ft.Text(f"{mes_rsd:.0f}", color="#69F0AE", size=11, width=90),
                ft.Text(f"{god_rsd:.0f}", color="#40C4FF", size=11, width=90),
            ], spacing=0),
            bgcolor=bg,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            border=ft.border.only(bottom=ft.BorderSide(1, "#1A1A1A")),
        )

    # ── IZRAČUNAJ ────────────────────────────────────────────
    def izracunaj(e):
        error_text.visible = False
        result_rows.controls.clear()
        summary_tf.value = ""
        total_power_text.value = "—"
        boiler_text.value = "—"
        safety_text.value = ""

        try:
            ukupna_pov = float(pov_tf.value) if pov_chk.value else None
        except Exception:
            error_text.value = "Neispravna vrednost za ukupnu površinu."
            error_text.visible = True
            page.update()
            return

        try:
            visina = float(vis_tf.value) if vis_chk.value else 2.7
        except Exception:
            visina = 2.7

        try:
            total_radiators = int(rad_tf.value) if rad_chk.value else 0
        except Exception:
            total_radiators = 0

        # Globalni faktori
        factor_global = 1.0
        if op_izol_mat_chk.value:
            factor_global *= ISOLATION_MATERIAL_FACTORS.get(op_izol_mat_dd.value, 1.0)
        if op_izol_deb_chk.value:
            factor_global *= ISOLATION_THICKNESS_FACTORS.get(op_izol_deb_dd.value, 1.0)
        if un_izol_mat_chk.value:
            factor_global *= ISOLATION_MATERIAL_FACTORS.get(un_izol_mat_dd.value, 1.0)
        if un_izol_deb_chk.value:
            factor_global *= ISOLATION_THICKNESS_FACTORS.get(un_izol_deb_dd.value, 1.0)
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
        if floors_chk.value:
            factor_global *= FLOOR_COUNT_FACTORS.get(floors_dd.value, 1.0)

        uf_factor = UNDERFLOOR_HEATING_FACTORS.get(uf_dd.value, 1.0) if uf_chk.value else 1.0

        ceil_iso_factor = ISOLATION_MATERIAL_FACTORS.get(ceil_izol_mat_dd.value, 1.0) if ceil_izol_mat_chk.value else 1.0
        if ceil_izol_deb_chk.value:
            ceil_iso_factor *= ISOLATION_THICKNESS_FACTORS.get(ceil_izol_deb_dd.value, 1.0)

        total_w = 0.0
        rooms_details = []

        if rooms_count_chk.value:
            for idx, rb in enumerate(room_blocks, start=1):
                if not rb['enabled'].value:
                    rb['result_text'].value = ""
                    rb['result_text'].update()
                    continue

                try:
                    area = float(rb['area'].value or 0)
                    window_area = float(rb['window_area'].value or 0)
                except Exception:
                    error_text.value = f"Greška u vrednostima za Soba {idx}."
                    error_text.visible = True
                    page.update()
                    return

                percent = (window_area / area * 100.0) if area > 0 else 0.0
                wfactor = window_percent_factor(percent)
                wglass_factor = WINDOW_TYPE_FACTORS.get(rb['window_type'].value, 1.0)

                room_factor = wfactor * wglass_factor * uf_factor * ceil_iso_factor
                room_base_w = BASE_W_PER_M2 * area * (visina / 2.7)
                room_required_w = room_base_w * room_factor * factor_global

                # Ventilacioni gubici
                volume = area * visina
                q_vent = 0.34 * (volume * 0.5) * DELTA_T
                room_required_w += q_vent * factor_global

                total_w += room_required_w
                rb['result_text'].value = f"≈ {room_required_w:.0f} W"
                rb['result_text'].update()

                rooms_details.append({
                    'index': idx, 'area': area,
                    'window_area': window_area, 'window_percent': percent,
                    'window_type': rb['window_type'].value,
                    'floor_type': rb['floor_type'].value,
                    'room_required_w': room_required_w,
                })

        if not rooms_details:
            error_text.value = "Nema uključenih soba za proračun."
            error_text.visible = True
            page.update()
            return

        ukupni_kw_exact   = total_w / 1000.0
        ukupni_kw_safe    = ukupni_kw_exact * SAFETY_FACTOR
        ukupni_kw_display = ceil(ukupni_kw_safe * 100) / 100.0
        kotao_preporuka   = nearest_commercial_boiler(ukupni_kw_display)

        total_power_text.value = f"{ukupni_kw_display:.2f} kW"
        boiler_text.value = f"Preporučeni kotao: {kotao_preporuka} kW"
        safety_text.value = (f"Bez rezerve: {ukupni_kw_exact:.2f} kW  |  "
                             f"Sa 15% rezervom: {ukupni_kw_safe:.2f} kW")

        try:
            cena_input = float(price_tf.value) if price_chk.value else None
        except Exception:
            cena_input = None

        result_rows.controls.append(result_header_row())
        for i, (fuel, price_default) in enumerate(FUEL_PRICES.items()):
            if not fuel_checkboxes[fuel].value:
                continue

            eff = FUEL_EFFICIENCY.get(fuel, 1.0)
            required_kw = ukupni_kw_safe / eff
            required_kw = ceil(required_kw * 100) / 100.0
            kotao_fuel  = nearest_commercial_boiler(required_kw)
            godisnja_kwh = required_kw * HEATING_HOURS
            mesecna_kwh  = godisnja_kwh / 6
            cena         = cena_input if cena_input is not None else price_default
            mes_rsd      = mesecna_kwh * cena
            god_rsd      = godisnja_kwh * cena

            result_rows.controls.append(
                make_result_row(fuel, required_kw, kotao_fuel, mesecna_kwh, mes_rsd, god_rsd, i % 2 == 0)
            )

        # Rezime
        lines = []
        lines.append("═" * 56 + "\n")
        lines.append("  KALKULATOR TOPLOTNE ENERGIJE — IZVEŠTAJ\n")
        lines.append("  Autor: Vasilije Stojiljković | ETS Nikola Tesla, Niš\n")
        lines.append("═" * 56 + "\n\n")
        lines.append(f"  Potrebna snaga (bez rezerve):    {ukupni_kw_exact:.3f} kW\n")
        lines.append(f"  Sa 15% sigurnosnom rezervom:     {ukupni_kw_safe:.3f} kW\n")
        lines.append(f"  Preporučena snaga kotla:          {kotao_preporuka} kW\n")
        if ukupna_pov:
            lines.append(f"  Ukupna površina objekta:         {ukupna_pov} m²\n")
        lines.append(f"  Visina plafona:                   {visina} m\n")
        lines.append(f"  Ukupan broj radijatora:           {total_radiators}\n\n")
        lines.append("─" * 56 + "\n")
        lines.append("  DETALJI PO SOBAMA:\n")
        lines.append("─" * 56 + "\n")
        for rd in rooms_details:
            lines.append(f"\n  Soba {rd['index']}: {rd['area']} m²"
                         f" | Prozori: {rd['window_area']} m² ({rd['window_percent']:.1f}%)\n")
            lines.append(f"    Tip prozora: {rd['window_type']}\n")
            lines.append(f"    Vrsta poda:  {rd['floor_type']}\n")
            lines.append(f"    ► Procena:   {rd['room_required_w']:.0f} W ({rd['room_required_w']/1000:.2f} kW)\n")
        lines.append("\n" + "─" * 56 + "\n")
        lines.append("  KORIŠĆENI PARAMETRI:\n")
        lines.append("─" * 56 + "\n")
        if matz_chk.value:          lines.append(f"  Materijal zidova:     {matz_dd.value}\n")
        if th_chk.value:            lines.append(f"  Debljina zidova:      {th_dd.value}\n")
        if orient_chk.value:        lines.append(f"  Orijentacija:         {orient_dd.value}\n")
        if btype_chk.value:         lines.append(f"  Vrsta objekta:        {btype_dd.value}\n")
        if floors_chk.value:        lines.append(f"  Spratnost:            {floors_dd.value}\n")
        if roof_chk.value:          lines.append(f"  Tip krova:            {roof_dd.value}\n")
        if uf_chk.value:            lines.append(f"  Podno grejanje:       {uf_dd.value}\n")
        if uf_area_chk.value:       lines.append(f"  Površina pod. grej.:  {uf_area_tf.value} m²\n")
        if op_izol_mat_chk.value:   lines.append(f"  Spoljna izolacija:    {op_izol_mat_dd.value} — {op_izol_deb_dd.value} cm\n")
        if un_izol_mat_chk.value:   lines.append(f"  Unutr. izolacija:     {un_izol_mat_dd.value} — {un_izol_deb_dd.value} cm\n")
        if ceil_izol_mat_chk.value: lines.append(f"  Izolacija plafona:    {ceil_izol_mat_dd.value} — {ceil_izol_deb_dd.value} cm\n")
        lines.append(f"\n  Sigurnosna rezerva: 15%\n")
        lines.append(f"  Grejna sezona:      {HEATING_HOURS}h/god (~150 dana)\n")
        lines.append(f"  ΔT proračuna:       {DELTA_T}K (Srbija)\n")

        summary_tf.value = "".join(lines)
        page.update()

    # ── LAYOUT ───────────────────────────────────────────────
    left_card = ft.Card(
        content=ft.Container(
            content=ft.Column(controls=[
                section_title("OPŠTI PODACI OBJEKTA"),
                pov_row, vis_row, sprat_row, btype_row, floors_row,
                ft.Row(controls=[
                    rooms_count_chk,
                    ft.Text("Broj soba:", color=TEXT_SEC, size=11, width=230),
                    rooms_count_tf,
                ], spacing=5),
                ft.Divider(color=BORDER, height=8),
                section_title("ZIDOVI I KONSTRUKCIJA"),
                matz_row, th_row, orient_row, roof_row,
                ft.Divider(color=BORDER, height=8),
                section_title("SPOLJNA IZOLACIJA"),
                op_izol_mat_row, op_izol_deb_row,
                section_title("UNUTRAŠNJA IZOLACIJA"),
                un_izol_mat_row, un_izol_deb_row,
                section_title("IZOLACIJA PLAFONA"),
                ceil_izol_mat_row, ceil_izol_deb_row,
                ft.Divider(color=BORDER, height=8),
                section_title("GREJANJE I TROŠKOVI"),
                uf_row, uf_area_row, price_row, rad_row,
                ft.Divider(color=BORDER, height=4),
                ft.Text("☑ Zeleno = aktivan   ☒ Crveno = isključen",
                        color=TEXT_MUTED, size=9, italic=True),
            ], spacing=3, scroll=ft.ScrollMode.AUTO),
            padding=14, bgcolor=BG_CARD,
        ),
        elevation=4,
    )

    rooms_card = ft.Card(
        content=ft.Container(
            content=ft.Column(controls=[
                section_title("SOBE"),
                ft.Text("Površina se automatski raspoređuje (ukupna ÷ broj soba). Možeš ručno izmeniti.",
                        color=TEXT_MUTED, size=9, italic=True),
                rooms_column,
            ], spacing=6, scroll=ft.ScrollMode.AUTO),
            padding=14, bgcolor=BG_CARD,
        ),
        elevation=4,
    )

    fuels_card = ft.Card(
        content=ft.Container(
            content=ft.Column(controls=[
                section_title("GORIVA"),
                ft.Column(controls=fuel_chk_controls, spacing=3),
            ], spacing=4),
            padding=14, bgcolor=BG_CARD,
        ),
        elevation=4,
    )

    calc_btn = ft.Container(
        content=ft.ElevatedButton(
            content=ft.Row(controls=[
                ft.Icon(ft.Icons.CALCULATE, color="#000000", size=20),
                ft.Text("IZRAČUNAJ", color="#000000", size=14, weight=ft.FontWeight.BOLD),
            ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            on_click=izracunaj,
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ACCENT2, ft.ControlState.HOVERED: "#FF8C60"},
                overlay_color=ft.Colors.with_opacity(0.1, "#000000"),
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.padding.symmetric(horizontal=30, vertical=14),
            ),
            width=220, height=52,
        ),
        alignment=ft.alignment.Alignment(0, 0),
        padding=ft.padding.symmetric(vertical=6),
    )

    results_card = ft.Card(
        content=ft.Container(
            content=ft.Column(controls=[
                section_title("REZULTATI PRORAČUNA"),
                error_text,
                power_card,
                ft.Container(
                    content=result_rows,
                    bgcolor=BG_CARD2, border_radius=8,
                    border=ft.border.all(1, BORDER),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                ft.Divider(color=BORDER, height=8),
                section_title("DETALJAN IZVEŠTAJ"),
                summary_tf,
            ], spacing=6, expand=True),
            padding=14, bgcolor=BG_CARD, expand=True,
        ),
        elevation=4, expand=True,
    )

    footer = ft.Container(
        content=ft.Row(controls=[
            ft.Text("© 2025 Vasilije Stojiljković", color=TEXT_MUTED, size=10),
            ft.Text("·", color=TEXT_MUTED, size=10),
            ft.Text("ETS Nikola Tesla, Niš", color=TEXT_MUTED, size=10),
            ft.Text("·", color=TEXT_MUTED, size=10),
            ft.Text("Sigurnosna rezerva: 15%  |  ΔT=35K  |  Grejna sezona: 1800h/god",
                    color=TEXT_MUTED, size=10),
        ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
        bgcolor="#080808",
        padding=ft.padding.symmetric(horizontal=20, vertical=7),
        border=ft.border.only(top=ft.BorderSide(1, BORDER)),
    )

    body = ft.Container(
        content=ft.Row(controls=[
            ft.Container(
                content=ft.Column(controls=[left_card, rooms_card],
                                  spacing=8, scroll=ft.ScrollMode.AUTO, expand=True),
                expand=5,
            ),
            ft.VerticalDivider(width=1, color=BORDER),
            ft.Container(
                content=ft.Column(controls=[fuels_card, calc_btn, results_card],
                                  spacing=8, scroll=ft.ScrollMode.AUTO, expand=True),
                expand=4,
            ),
        ], expand=True, spacing=0, vertical_alignment=ft.CrossAxisAlignment.START),
        expand=True,
        padding=ft.padding.symmetric(horizontal=10, vertical=8),
    )

    # ── UVODNI EKRAN SA UPUTSTVOM ────────────────────────────
    def close_welcome(e):
        welcome_dlg.open = False
        page.update()

    welcome_dlg = ft.AlertDialog(
        modal=True,
        bgcolor=BG_CARD,
        title=ft.Row(controls=[
            ft.Icon(ft.Icons.INFO_OUTLINE, color=ACCENT, size=24),
            ft.Text("Kako koristiti kalkulator?", color=ACCENT,
                    size=16, weight=ft.FontWeight.BOLD),
        ], spacing=10),
        content=ft.Container(
            content=ft.Column(controls=[
                ft.Text("Pratite sledeće korake:", color=TEXT_PRI, size=13, weight=ft.FontWeight.BOLD),
                ft.Divider(color=BORDER, height=8),

                # Korak 1
                ft.Row(controls=[
                    ft.Container(
                        content=ft.Text("1", color="#000", size=12, weight=ft.FontWeight.BOLD),
                        bgcolor=ACCENT, width=24, height=24, border_radius=12,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Column(controls=[
                        ft.Text("Unesite opšte podatke o objektu", color=TEXT_PRI, size=12, weight=ft.FontWeight.BOLD),
                        ft.Text("Površina, visina plafona, vrsta objekta, spratnost", color=TEXT_SEC, size=11),
                    ], spacing=1, expand=True),
                ], spacing=10),

                # Korak 2
                ft.Row(controls=[
                    ft.Container(
                        content=ft.Text("2", color="#000", size=12, weight=ft.FontWeight.BOLD),
                        bgcolor=ACCENT, width=24, height=24, border_radius=12,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Column(controls=[
                        ft.Text("Podesite zidove, izolaciju i krov", color=TEXT_PRI, size=12, weight=ft.FontWeight.BOLD),
                        ft.Text("Materijal, debljina, izolacija spolja/unutra/plafon", color=TEXT_SEC, size=11),
                    ], spacing=1, expand=True),
                ], spacing=10),

                # Korak 3
                ft.Row(controls=[
                    ft.Container(
                        content=ft.Text("3", color="#000", size=12, weight=ft.FontWeight.BOLD),
                        bgcolor=ACCENT, width=24, height=24, border_radius=12,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Column(controls=[
                        ft.Text("Podesite broj soba", color=TEXT_PRI, size=12, weight=ft.FontWeight.BOLD),
                        ft.Text("Površina se automatski raspoređuje — možete je ručno izmeniti.\nZa svaku sobu unesite površinu prozora i tip prozora.", color=TEXT_SEC, size=11),
                    ], spacing=1, expand=True),
                ], spacing=10),

                # Korak 4
                ft.Row(controls=[
                    ft.Container(
                        content=ft.Text("4", color="#000", size=12, weight=ft.FontWeight.BOLD),
                        bgcolor=ACCENT, width=24, height=24, border_radius=12,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Column(controls=[
                        ft.Text("Izaberite goriva i unesite cenu energije", color=TEXT_PRI, size=12, weight=ft.FontWeight.BOLD),
                        ft.Text("Štiklirajte goriva za koja želite prikaz troškova", color=TEXT_SEC, size=11),
                    ], spacing=1, expand=True),
                ], spacing=10),

                # Korak 5
                ft.Row(controls=[
                    ft.Container(
                        content=ft.Text("5", color="#000", size=12, weight=ft.FontWeight.BOLD),
                        bgcolor=ACCENT2, width=24, height=24, border_radius=12,
                        alignment=ft.alignment.Alignment(0, 0),
                    ),
                    ft.Column(controls=[
                        ft.Text("Kliknite IZRAČUNAJ", color=ACCENT2, size=12, weight=ft.FontWeight.BOLD),
                        ft.Text("Dobijate preporučenu snagu kotla, mesečne i godišnje troškove po gorivu", color=TEXT_SEC, size=11),
                    ], spacing=1, expand=True),
                ], spacing=10),

                ft.Divider(color=BORDER, height=8),
                ft.Row(controls=[
                    ft.Icon(ft.Icons.CHECK_BOX_OUTLINED, color=GREEN, size=16),
                    ft.Text("Zeleni checkbox = parametar aktivan", color=TEXT_SEC, size=11),
                    ft.Container(width=16),
                    ft.Icon(ft.Icons.CHECK_BOX_OUTLINE_BLANK, color=RED, size=16),
                    ft.Text("Crveni = isključen", color=TEXT_SEC, size=11),
                ], spacing=6),
                ft.Text(
                    "Autor: Vasilije Stojiljković | ETS Nikola Tesla, Niš",
                    color=TEXT_MUTED, size=10, italic=True,
                ),
            ], spacing=10, width=480),
            padding=ft.padding.only(top=8),
        ),
        actions=[
            ft.ElevatedButton(
                content=ft.Row(controls=[
                    ft.Icon(ft.Icons.PLAY_ARROW, color="#000", size=18),
                    ft.Text("POČNI SA RADOM", color="#000", size=13, weight=ft.FontWeight.BOLD),
                ], spacing=6),
                on_click=close_welcome,
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ACCENT, ft.ControlState.HOVERED: "#00FF8C"},
                    shape=ft.RoundedRectangleBorder(radius=8),
                    padding=ft.padding.symmetric(horizontal=24, vertical=12),
                ),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
        shape=ft.RoundedRectangleBorder(radius=16),
    )
    page.overlay.append(welcome_dlg)
    # Prikaži uputstvo nakon što se splash zatvori (2.6s)
    threading.Timer(2.6, lambda: [setattr(welcome_dlg, 'open', True), page.update()]).start()

    page.add(ft.Column(controls=[header, body, footer], spacing=0, expand=True))
    page.update()


# ══════════════════════════════════════════════════════════════
#  POKRETANJE
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        port=8080,
        host="0.0.0.0",
    )

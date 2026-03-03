# Kalkulator Toplotne Energije — Uputstvo za Deploy

## Sadržaj foldera
```
KalkulatorGrejanja/
├── kalkulator_grejanja_flet.py   ← glavna aplikacija
├── requirements.txt               ← Python paketi
├── Dockerfile                     ← Docker konfiguracija
├── fly.toml                       ← Fly.io konfiguracija
├── README.md                      ← ovo uputstvo
└── assets/                        ← STAVI OVDE SVOJE SLIKE
    ├── ikonica.png                ← (stavi svoju sliku)
    └── ikonica.ico                ← (stavi svoju sliku)
```

---

## KORAK 1 — Dodaj svoje slike
Stavi `ikonica.png` i `ikonica.ico` u folder `assets/`.
Ako ne staviš slike, aplikacija radi normalno bez njih.

---

## KORAK 2 — Instaliraj Fly.io CLI
Otvori PowerShell kao Administrator i pokreni:
```
winget install flyctl
```
Zatvori i otvori novi terminal, pa proveri:
```
fly version
```

---

## KORAK 3 — Napravi Fly.io nalog (besplatno, bez kartice)
```
fly auth signup
```

---

## KORAK 4 — Deploy
U terminalu uđi u ovaj folder:
```
cd C:\putanja\do\KalkulatorGrejanja
```
Pokreni:
```
fly launch
```
Odgovori na pitanja:
- App name: kalkulator-grejanja (ili nešto drugo)
- Region: ams
- Dockerfile detected? → y
- PostgreSQL? → n
- Redis? → n

Zatim:
```
fly deploy
```

Za ~3 minuta imaš sajt na:
```
https://kalkulator-grejanja.fly.dev
```

---

## Svaki put kad menjaš kod
```
fly deploy
```

---

## Lokalno pokretanje (bez interneta)
```
pip install flet==0.24.1
python kalkulator_grejanja_flet.py
```

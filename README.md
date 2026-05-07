# VečerkaPlus Analytics

Analytický dashboard pro [VečerkaPlus](https://vecerkaplus.cz) — noční rozvoz alkoholu a snacků ve Frýdku-Místku (Pá+So 22:00–6:00).

## Proč tento projekt vznikl

VečerkaPlus provozuje zákaznickou aplikaci (React + Supabase + Vercel), která zpracovává objednávky v reálném čase. Chyběl ale nástroj pro analýzu byznysu: **jak se prodává, co má největší marži, kdy přicházejí objednávky, které produkty se kupují spolu**.

Tento projekt je separátní Python/Streamlit aplikace běžící na vlastním Ubuntu serveru, dostupná na `data.vecerkaplus.cz`. Čerpá data přímo ze sdílené Supabase databáze a poskytuje provozovateli přehled bez nutnosti sahat do produkčního kódu.

## Co umí

### 📦 Produkty
- KPI karty: počet produktů, kategorie, průměrná cena, hodnota skladu
- Sloupcový graf dle kategorie + histogram cen
- Karta každého produktu s **reálnou fotkou**, cenou a stavem skladu (🟢/🟡/🔴)
- Filtr dle kategorie a cenového rozsahu; přepínač karet / tabulky

### 💰 Marže & Ceník
- Upload CSV s nákupními cenami z Makra (nebo automatické načtení ukázkového souboru)
- **Fuzzy matching** (rapidfuzz, cutoff 70) — páruje názvy přes rozdíly v diakritice a formátu
- Výpočet marže, srovnání s cílovou marží (35 %), doporučené prodejní ceny
- Červené zvýraznění produktů pod cílovou marží

### 🛒 Objednávky
- **Live monitoring** s auto-refresh (15/30/60 s) a zvukovými notifikacemi při změně stavu:
  - 🔵 nová → 3× stoupající tón
  - 🟡 přijatá → 2× pípnutí
  - 🟢 doručená → dur fanfára
  - 🔴 zrušená → sestupný bzukot
- Denní tržby, heatmapa objednávek (den × hodina), platební metody
- Top 10 produktů dle prodaného množství
- **Market basket analýza** (Apriori) — které produkty se kupují spolu
- Toggle pro **demo data** (150 syntetických objednávek)

### 🏠 Home dashboard
- Shift status: OTEVŘENO / ZAVŘENO s časem příštího otevření
- Live KPI (tržby za 7 dní, průměrná objednávka, tržby celkem)
- Tabulka posledních objednávek + status breakdown

## Technický stack

```
Python 3.11+
├── streamlit       — UI
├── pandas          — ETL pipeline
├── plotly          — grafy
├── supabase-py     — databáze
├── rapidfuzz       — fuzzy matching
├── mlxtend         — market basket analýza (Apriori)
└── python-dotenv   — konfigurace
```

## Instalace

```bash
git clone https://github.com/<user>/vecerkaplus-analytics
cd vecerkaplus-analytics
pip install -r requirements.txt
cp .env.example .env
# Doplň SUPABASE_URL a SUPABASE_SERVICE_KEY
streamlit run app/Home.py --server.port 8501
```

## Konfigurace

```env
SUPABASE_URL=https://<project-id>.supabase.co
SUPABASE_SERVICE_KEY=<service_role_key>
```

> ⚠️ Používej **service role key** — RLS na tabulce `orders` neumožňuje anonymní SELECT.

## Struktura projektu

```
app/
  Home.py               # Dashboard + live monitoring
  pages/
    1_Produkty.py       # Přehled skladu s fotkami
    2_Marze_a_Cenik.py  # Analýza marží
    3_Objednavky.py     # Sales analytics
src/
  config.py             # Konstanty
  supabase_client.py    # Supabase client
  etl/
    load.py             # Načítání z DB
    clean.py            # Čištění dat
    transform.py        # Transformace (heatmap, top produkty...)
    demo_data.py        # Generátor syntetických objednávek
data/
  makro_sample.csv      # Ukázkový ceník Makro
```

## Deployment

```bash
# systemd service
streamlit run app/Home.py --server.port 8501 --server.headless true
# dostupné přes Cloudflare Tunnel na data.vecerkaplus.cz
```

## Plánované rozšíření

- **Fáze 2** — Telegram bot + Google Vision OCR faktur
- **Fáze 3** — Real-time sklad, forecast spotřeby, alert před směnou
- **Fáze 4** — Rozvozová analytika (Google Distance Matrix, čistý zisk/objednávku)
- **Fáze 5** — Integrace do `/admin` panelu na vecerkaplus.cz

## Licence

MIT

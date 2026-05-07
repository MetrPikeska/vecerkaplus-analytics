# VečerkaPlus — Vize projektu (dash.vecerkaplus.cz)

> Tento dokument popisuje konečný cíl projektu. Slouží jako kontext pro vývoj.
> Aktuální stav je MVP (semestrální práce), vize je dlouhodobý cíl.

---

## Co to je

Analytický a operační dashboard pro [VečerkaPlus](https://vecerkaplus.cz) —
noční rozvoz alkoholu a snacků ve Frýdku-Místku (Pá–Ne, 22:00–6:00).

### Rozdělení systému

| | vecerkaplus.cz/admin | dash.vecerkaplus.cz |
|---|---|---|
| Účel | Operativa | Analytika + přehled |
| Stack | React + Vite + Vercel | Python + Streamlit + Ubuntu |
| Co tam dělám | Přijímám objednávky, měním statusy, spravuji produkty | Sleduji marže, analytiku, kurýra, sklad |
| Realtime | Objednávky (poll 30s) | Kurýr tracking (Supabase Realtime) |

---

## Deployment

```
dash.vecerkaplus.cz
        ↓
Cloudflare Tunnel (cloudflared daemon)
        ↓
localhost:8501
        ↓
Streamlit app (systemd: vecerkaplus-dash.service)
        ↓
Ubuntu server (vlastní)
```

---

## Moduly (fáze vývoje)

### Fáze 1 — MVP (semestrální práce) ✅
Streamlit dashboard se 3 stránkami:
- **Produkty** — přehled skladu a cen ze Supabase
- **Marže & Ceník** — výpočet marží z Makro CSV vs. prodejní ceny
- **Objednávky** — sales dashboard, heatmapa, market basket analýza

### Fáze 2 — Faktury OCR 📸
Automatické zpracování nákupních faktur z Makra přes Telegram:
- Majitel vyfotí fakturu → pošle do Telegram botu
- Bot → Google Vision API → OCR → parser (název, cena/ks, množství)
- Fuzzy match na produkty v Supabase
- Uloží do tabulky `purchases` v Supabase
- Bot odpoví: "Zpracováno: 36 položek, celkem 23 046 Kč"
- Dashboard se automaticky aktualizuje

### Fáze 3 — Sklad & Doplňování 📦
- Real-time stav skladu po každém nákupu (OCR) a prodeji (orders)
- Forecast spotřeby: kolik kusů se prodá za jeden víkend
- Alert před směnou: "Dokup Red Bull (zbývá 3 ks, očekávaná spotřeba 8 ks)"
- Doporučený nákupní seznam před každým víkendem

### Fáze 4 — Rozvozová analytika 🗺️
Per-objednávka analýza nákladů a ziskovosti:
- Vzdálenost v km (Google Distance Matrix API — klíč existuje)
- Náklady rozvoz (km × spotřeba × cena benzínu)
- Čistý zisk = tržby − nákupní ceny − náklady rozvoz
- Heatmapa poptávky ve Frýdku-Místku
- Optimální pokrytí doručovací zóny

### Fáze 5 — Live Kurýr Tracking 🚗
Real-time sledování kurýra pro zákazníka i dispečera:

**Kurýrova React Native app (iPhone):**
- Jednoduchá pracovní aplikace na ploše iPhonu
- GPS poloha → Supabase Realtime každých 5–10s
- Zobrazí aktivní objednávku, adresu zákazníka

**vecerkaplus.cz (zákazník):**
- Rozšíření existujícího order trackeru
- Leaflet mapa s live marker kurýra
- Přepočet vzdálenosti a ETA v reálném čase

**dash.vecerkaplus.cz (dispečer):**
- Live mapa s polohou kurýra
- Historie tras per objednávka
- Průměrné doby doručení podle zóny

### Fáze 6 — Správa produktů a objednávek v dashu 🔧
Přesun části operativy z /admin do dashu:
- Úprava cen přímo z pohledu marže
- Správa skladu po nákupu
- Přehled objednávek s nákladovou analytikou

---

## Datové zdroje

| Zdroj | Obsah | Přístup |
|---|---|---|
| Supabase products | Produkty, ceny, sklad | supabase-py (service key) |
| Supabase orders | Objednávky, items JSONB, stavy | supabase-py (service key) |
| Supabase purchases | Nákupní faktury (Fáze 2) | supabase-py (service key) |
| Supabase courier_location | GPS poloha kurýra (Fáze 5) | Supabase Realtime |
| Makro CSV / OCR | Nákupní ceny | CSV upload nebo Telegram bot |
| Google Vision API | OCR faktur | REST API |
| Google Distance Matrix | Vzdálenosti rozvozu | REST API (klíč existuje) |
| Telegram Bot | Příjem fotek faktur | Bot token existuje |

---

## Supabase schéma (aktuální + plánované)

```sql
-- Existující
products         (id UUID, name, category, price INT, stock INT, emoji, img)
orders           (id UUID, created_at, name, address, phone, payment,
                  items JSONB, total INT, status, note)

-- Fáze 2
purchases        (id UUID, created_at, invoice_date, supplier TEXT,
                  product_name TEXT, product_id UUID FK,
                  buy_price_per_unit NUMERIC, quantity INT,
                  total_cost NUMERIC, source TEXT)

-- Fáze 5
courier_location (id UUID, created_at, order_id UUID FK,
                  lat NUMERIC, lng NUMERIC, updated_at TIMESTAMPTZ)
```

---

## Technický stack

```
Ubuntu server
├── Streamlit app (port 8501)                    → dash.vecerkaplus.cz
│   ├── Python 3.11+
│   ├── pandas, plotly, supabase-py
│   ├── rapidfuzz, mlxtend
│   └── systemd: vecerkaplus-dash.service
├── Telegram bot (python-telegram-bot)           → OCR faktur (Fáze 2)
│   ├── Google Vision API
│   └── systemd: vecerkaplus-bot.service
└── Cloudflare Tunnel (cloudflared)
    └── dash.vecerkaplus.cz → localhost:8501

iPhone kurýra (Fáze 5)
└── React Native app
    └── GPS → Supabase Realtime → zákazník/dash
```

---

## Aktuální priorita

**Fáze 1 dokončit do 8. 5. 2026 23:59** (deadline semestrální práce).
Fáze 2–6 jsou post-deadline rozšíření pro reálné nasazení.

### Fáze 7 — Scraping akcí & Cílení reklamy 🎯
Sledování událostí ve Frýdku-Místku pro lepší cílení marketingu:

**Zdroje dat:**
- Facebook Events API (omezený přístup) nebo scraping veřejných FB akcí
- Eventbrite API (spolehlivější, veřejné akce)
- Ruční zadání akce v dashu jako fallback

**Co se zobrazí v dashu:**
- Mapa FM s vrstvami: akce tento víkend + heatmapa historických objednávek
- Překryv = kde se potkávají akce a poptávka
- Seznam akcí s počtem účastníků, adresou, datem

**Doporučovací engine:**
- "Tuto sobotu je akce na Střelnici (~300 lidí) — zvýš dosah reklamy v okruhu 1 km"
- Automatický alert před víkendem pokud je v FM velká akce
- Export: seznam ulic/čtvrtí pro cílení FB/Instagram reklamy

**Stack:**
- Scraping: Puppeteer nebo requests + BeautifulSoup
- Geocoding: Google Geocoding API (klíč existuje)
- Mapa: Leaflet (už v projektu)
- Alerts: Telegram bot (už existuje)
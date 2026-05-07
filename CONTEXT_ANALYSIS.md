# VečerkaPlus Analytics — Vize projektu

> Tento dokument popisuje konečný cíl projektu. Slouží jako kontext pro vývoj.
> Aktuální stav je MVP (semestrální práce), vize je dlouhodobý cíl.

---

## Co to je

Datová a analytická extenze pro [VečerkaPlus](https://vecerkaplus.cz) —  
noční rozvoz alkoholu a snacků ve Frýdku-Místku (Pá–Ne, 22:00–6:00).

Hlavní projekt běží na **React + Vite + Supabase + Vercel**.  
Tato extenze je **separátní Python aplikace** běžící na vlastním Ubuntu serveru,  
dostupná na `data.vecerkaplus.cz` přes Cloudflare Tunnel.

---

## Konečný cíl

Plně automatizovaný business intelligence nástroj pro majitele VečerkaPlus,
který pokryje celý cyklus: **nákup → sklad → prodej → analýza → rozhodnutí**.

---

## Moduly (fáze vývoje)

### Fáze 1 — MVP (semestrální práce) ✅
Streamlit dashboard se 3 stránkami:
- **Produkty** — přehled skladu a cen ze Supabase
- **Marže & Ceník** — výpočet marží z Makro CSV vs. prodejní ceny
- **Objednávky** — sales dashboard, heatmapa, market basket analýza

### Fáze 2 — Faktury OCR 📸
Automatické zpracování nákupních faktur z Makra:
- Majitel vyfotí fakturu a pošle ji do **Telegram botu**
- Bot předá fotku **Google Vision API** → OCR → strukturovaná data
- Parser extrahuje: název produktu, cena/ks, počet kusů, celkem
- Fuzzy match na produkty v Supabase
- Uloží do tabulky `purchases` v Supabase
- Bot odpoví potvrzením: *"Zpracováno: 36 položek, celkem 23 046 Kč"*
- Dashboard se automaticky aktualizuje

### Fáze 3 — Sklad & Doplňování 📦
- Real-time stav skladu po každém nákupu (z OCR) a prodeji (z orders)
- Forecast spotřeby: kolik kusů se typicky prodá za jeden víkend
- Alert před směnou: *"Dokup Red Bull (zbývá 3 ks, očekávaná spotřeba 8 ks)"*
- Doporučený nákupní seznam před každým víkendem

### Fáze 4 — Rozvozová analytika 🗺️
Per-objednávka analýza:
- Vzdálenost v km (Google Distance Matrix API — klíč už existuje)
- Odhadované náklady rozvoz (km × spotřeba × cena benzínu)
- Čistý zisk na objednávku = tržby − nákupní ceny − náklady rozvoz
- Heatmapa poptávky ve Frýdku-Místku (kde zákazníci objednávají)
- Optimální pokrytí doručovací zóny

### Fáze 5 — Admin integrace 🔗
Propojení s existujícím `/admin` panelem na vecerkaplus.cz:
- Sekce `/admin/analytics` přímo v React aplikaci
- Iframe nebo API volání na data.vecerkaplus.cz
- Nebo přepsat relevantní části do React komponent

---

## Datové zdroje

| Zdroj | Obsah | Přístup |
|---|---|---|
| Supabase `products` | Produkty, ceny, sklad | supabase-py (service key) |
| Supabase `orders` | Objednávky, items JSONB, stavy | supabase-py (service key) |
| Supabase `purchases` | Nákupní faktury (budoucí) | supabase-py (service key) |
| Makro CSV / OCR | Nákupní ceny | CSV upload nebo Telegram bot |
| Google Vision API | OCR faktur | REST API |
| Google Distance Matrix | Vzdálenosti rozvozu | REST API (klíč existuje) |
| Telegram Bot | Příjem fotek faktur, notifikace | Bot token existuje |

---

## Technický stack

```
Ubuntu server
├── Streamlit app (port 8501)
│   ├── Python 3.11+
│   ├── pandas, plotly, supabase-py
│   ├── rapidfuzz, mlxtend
│   └── systemd service
├── Telegram bot (python-telegram-bot)
│   ├── Příjem fotek → Google Vision OCR
│   ├── Parser faktur (Makro formát)
│   └── systemd service
└── Cloudflare Tunnel (cloudflared)
    └── data.vecerkaplus.cz → localhost:8501
```

---

## Supabase schéma (aktuální + plánované)

```sql
-- Existující
products (id UUID, name, category, price INT, stock INT, emoji, img)
orders   (id UUID, created_at, name, address, phone, payment,
          items JSONB, total INT, status, note)

-- Plánované (Fáze 2)
purchases (id UUID, created_at, invoice_date, supplier TEXT,
           product_name TEXT, product_id UUID FK,
           buy_price_per_unit NUMERIC, quantity INT,
           total_cost NUMERIC, source TEXT) -- 'csv' nebo 'ocr'
```

---

## Deployment

```
data.vecerkaplus.cz
        ↓
Cloudflare Tunnel (cloudflared daemon)
        ↓
localhost:8501
        ↓
Streamlit app (systemd: vecerkaplus-analytics.service)
```

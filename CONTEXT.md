# VečerkaPlus

Noční rozvoz alkoholu, piva, cigaret a snacků ve Frýdku-Místku a okolí (Pá–So 22:00–6:00). Zákazník zadá adresu, systém ověří dosah, zákazník složí košík a odešle objednávku — kurýr dorazí do ~60 min.

## Language

**Objednávka** (Order):
Jediná transakční entita v systému. Vzniká odesláním košíku, patří zákazníkovi a prochází stavovým strojem až do doručení nebo zrušení.
_Avoid_: nákup, transakce, požadavek

**Položka objednávky** (Order item):
Jeden produkt v konkrétním množství uvnitř objednávky. Uložena jako JSONB v sloupci `items`.
_Avoid_: produkt v košíku, řádek objednávky

**Produkt** (Product):
Zboží nabízené k prodeji. Má kategorii, cenu a stav skladu.
_Avoid_: zboží, item, položka

**Party Mix**:
Předpřipravený balíček produktů prodávaný jako jedna položka za pevnou cenu (např. sada pro 4 osoby). V systému je to běžný produkt s `category = "Party Mix"`. Složení balíčku není strojově sledováno — je součástí názvu/popisu produktu.
_Avoid_: bundle, set, sada

**Sklad** (Stock):
Počet kusů dostupných k prodeji pro daný produkt. Dekrementuje se serverovou triggerem při potvrzení objednávky.
_Avoid_: inventář, zásoba

**Zákazník** (Customer):
Osoba, která odešle objednávku. Není evidována jako samostatná entita — identifikuje se jménem a telefonem přímo na objednávce.
_Avoid_: uživatel, klient, účet

**Operátor** (Operator):
Osoba monitorující admin panel pro nové objednávky a spravující jejich stav. V systému není samostatnou entitou — identifikuje se sdíleným admin heslem. Může, ale nemusí být zároveň kurýrem.
_Avoid_: admin, dispečer

**Kurýr** (Courier):
Osoba fyzicky doručující objednávky. Má přístup do admin panelu (sdílené heslo) a může sám měnit stav objednávek. V systému není entitou — komunikuje přes Telegram notifikace.
_Avoid_: řidič, doručovatel

**Dosah doručení** (Delivery range):
Maximální vzdálenost (20 km po silnici od FM) ve které systém povolí odeslání objednávky. Ověřuje se přes Google Distance Matrix API.
_Avoid_: doručovací zóna, oblast doručení

**Košík** (Cart):
Dočasná kolekce položek sestavená zákazníkem před odesláním objednávky. Uložen v `localStorage`.
_Avoid_: nákupní košík (redundantní)

## Order lifecycle

```
nová → přijatá → doručená
         ↓           ↓
       zrušená    zrušená
nová → zrušená
```

- **nová**: objednávka přijata systémem, čeká na akci kurýra/admina
- **přijatá**: kurýr/admin potvrdil a vezme ji na cestu
- **doručená**: zákazník obdržel zásilku
- **zrušená**: objednávka stornována — dosažitelná z jakéhokoliv stavu

**Pravidla přechodů:**
- Přechody jsou jednosměrné (nelze vrátit zpět): nová → přijatá → doručená
- `zrušená` je dosažitelná z jakéhokoliv stavu
- Pouze admin může měnit stav — zákazník nemůže stornovat

## Operating hours

- Provoz: **pátek a sobota v noci**, 22:00 → 06:00 následujícího rána
- Výjimka: provoz také ve státní svátky (přesná pravidla viz níže)
- Neděle **není** pravidelný provozní den
_Avoid_: "pátek–neděle", "Fri–Sun"

**Státní svátky** (navíc ke standardnímu pátku+sobotě):
- Jede: svátek padne na **čtvrtek nebo pátek**
- Nejede: pondělí, středa, ostatní mid-week svátky
- Vždy jede bez ohledu na den: **Vánoce** a **Silvestr**
- Aktuální výjimky oznamovány na Instagramu a Telegramu VečerkaPlus

## Payment methods

- **Hotově při doručení** — fyzická hotovost kurýrovi
- **Kartou při doručení** — aktuálně QR kód (bankovní převod přes QR), v budoucnu fyzický terminál
_Avoid_: "online platba", "platba předem"

## Pricing rules

- Minimální objednávka: 500 Kč
- Doprava zdarma od: 1 000 Kč
- Poplatek za dopravu: 39 Kč (při objednávce pod 1 000 Kč)

## Relationships

- Objednávka obsahuje 1–N **položek objednávky**
- Objednávka patří jednomu **zákazníkovi** (identifikace jménem + telefonem)
- Objednávka má právě jeden stav v daném čase

## Operator notifications (implemented)

Při nové objednávce odchází 3 kanály paralelně:
1. **Email** (Resend → vecerkaplus@gmail.com) — plný přehled vč. navigačního linku a ETA
2. **Telegram** — kompaktní zpráva se stejnými daty
3. **Hovor** (Twilio Studio Flow) — hlasová notifikace na pracovní telefon (`TWILIO_TO_NUMBER`)

Všechny kanály obsahují `note` zákazníka (pokud vyplněna). Hovor selžení nezastaví odpověď zákazníkovi — fallback je tichý.

**Twilio debugging**: `busy` status = volaný telefon byl obsazený (ne chyba integrace). Ověřit v Twilio Console → Studio → Execution Logs.

## Missing features (known gaps)

- **Zákaznické notifikace**: zákazník nedostává žádné oznámení o změně stavu objednávky — pouze polluje tracker. Plánované: email + push notifikace při změně na `přijatá` a `doručená`. Viz GitHub Issue #10.
- ~~**Poznámka v notifikacích**~~: ✅ Pole `note` je již v Telegram i email notifikacích.
- **Jednosměrný stavový stroj**: admin panel umožňuje libovolné přechody — viz ADR-0001.
- **Auto-pin při distance check**: `/api/distance` nevrací geocoded souřadnice — `map_pin` se nenastaví automaticky pro ručně zadané adresy (pouze při autocomplete nebo GPS). Kurýr pak dostane jen textovou adresu bez navigačního linku.
- **Skrytí produktu**: neexistuje způsob jak produkt dočasně skrýt bez smazání — jedinou možností je nastavit `stock = 0` (ale produkt zůstane viditelný jako "Vyprodáno").
- **Retention policy (GDPR)**: objednávky se uchovávají donekonečna. Doporučení: po 12 měsících anonymizovat osobní údaje (`name`, `phone`, `address` → NULL nebo "anonymized"), zachovat `total`, `items`, `status` pro statistiky. Implementovat jako Supabase pg_cron job spouštěný měsíčně.
- **Inventura skladu**: stock hodnoty v DB jsou nepřesné — inventura se dlouho nedělala. Trigger `decrement_stock()` odečítá správně, ale výchozí stavy nejsou spolehlivé. Aktualizace probíhá přímou editací v Supabase, ne přes admin panel.

## Pending code fixes

- [x] `App.jsx`: smazat hardcoded fallback katalog produktů — Supabase je zdroj pravdy
- [x] `index.html` FAQ: opravit "každý pátek, sobotu a neděli" → "pátek a sobotu, také o svátcích"
- [x] `supabase/fix-security.sql`: trigger threshold opravit 500 → 1000 Kč (doprava zdarma od 1000 Kč)
- [ ] `Admin.jsx` stavový select: vynutit jednosměrné přechody (nová→přijatá→doručená, zrušená z čehokoliv)
- [ ] Supabase: spustit opravený `fix-security.sql` v SQL Editoru (trigger v DB je stále starý)

## Example dialogue

> **Dev:** "Zákazník mi říká, že objednávka nebyla doručena — chce ji stornovat."
> **Ops:** "Přepni ji na `zrušená` v admin panelu. Zákazník to neuvidí okamžitě, ale tracker se aktualizuje do 15 sekund."

> **Dev:** "Mám přidat produkt 'Víno rosé' do nabídky — do jaké kategorie?"
> **Ops:** "Buď do 'Víno', nebo jako součást 'Party Mix' balíčku. Party Mix jsou předpřipravené sady, ne jednotlivé produkty."

> **Dev:** "Proč nejezdíte v pondělí po svátcích?"
> **Ops:** "Jezdíme jen na svátky, které prodlužují víkend dopředu — čtvrtek nebo pátek. Pondělí je po víkendu, lidi jsou zpátky v práci. Výjimka jsou Vánoce a Silvestr — tam jedeme vždy."

## Flagged ambiguities

- Stav přechodů: kód momentálně umožňuje libovolné přechody (select bez omezení) — rozhodnuto, že se má vynutit jednosměrný tok (nová→přijatá→doručená), zrušená z jakéhokoliv stavu. Oprava zatím není implementována.

## Design Context

### Users

Zákazníci VečerkaPlus jsou 18–40letí lidé v době noční zábavy — studenti na domácím dýchánku, dospělí na neformální oslavě, lidi vracející se z podniku. Objednávají **pozdě v noci**, pravděpodobně na mobilu, pod vlivem alkoholu nebo ve spěchu. Potřebují projít od "chci pivo" k "objednáno" co nejrychleji s minimálním třením. Nejde jim o estetický zážitek — jde jim o rychlost, jistotu, že to funguje, a dobrý pocit z toho, že to vypadá seriózně.

Sekundární uživatel: **administrátor** (provozovatel / kurýr) — sleduje příchozí objednávky, mění statusy, spravuje produkty. Pracuje pod tlakem (noc, objednávky přicházejí v reálném čase).

### Brand Personality

**Rychlý. Diskrétní. Spolehlivý.**

Tón: přátelský profík — ne formální, ne hloupě "cool", ne fastfood. Jako dobrý barman: přívětivý, efektivní, bez zbytečných slov. Trochu humoru je v pořádku (emoji 🛵, "Na zdraví!"), ale interface má působit jako fungující servis, ne jako studentský projekt.

Nesmí vypadat amatérsky. Nejdůležitější kritérium kvality je: "Vypadá tohle jako reálný profesionální byznys?" — ne "Vypadá tohle moderně?".

### Aesthetic Direction

- **Barevné téma**: tmavé pozadí (`#0a0a0f` nebo blízko) + zlatý akcent (`#d4af6a`). Zachovat. Zlatá=prémiové, tmavá=noční atmosféra. Dobře zvoleno pro cílovou skupinu i kontext.
- **Vizuální tón**: mezi "prémiová noční doručovací služba" a "spolehlivý lokální servis" — ne luxusní bar, ne rozvoz pizzy. Někde mezi Uber Eats (spolehlivost) a lokální pivnice (přátelskost).
- **Anti-reference**: fastfood korporát, lékárna/klinika čistota, přehnaně luxusní/clubbing vibe, studentský projekt (pixelované emoji jako jediný vizuální prvek).
- **Typografie**: Libre Baskerville pro display (ceny, nadpisy) — zachovat, dává prémiový nádech. DM Sans pro body text — funkční, ale lze vylepšit.
- **Animace**: minimálně. Jen funkční stavové přechody (košík, potvrzení objednávky). Zrušit dekorativní pulzující tečky všude.

### Design Principles

1. **Rychlost nad vším** — každý krok k dokončení objednávky musí být co nejkratší. Žádné zbytečné obrazovky, žádné překážky. Zákazník v 1:30 ráno nechce číst.

2. **Profesionalita jako důvěra** — zákazník platí cash kurýrovi, kterého nezná. Interface musí budit důvěru: čisté, konzistentní, bez amatérských chyb (překlepy, rozbitý layout, chybějící stavy).

3. **Noční kontext** — tmavé téma není jen estetika, je to správná volba pro použití ve tmě. Kontrast musí být vysoký. Žádné slabě viditelné texty na dark pozadí.

4. **Animace slouží stavu, ne dekoraci** — pulzující tečky, glowing efekty a animované bannery jsou hluk. Pohyb je vyhrazen pro: potvrzení akce, změnu stavu objednávky, přechod view.

5. **Mobile-first, thumb-friendly** — primární zákazník má telefon v ruce (možná v druhé pivo). Klíčové akce patří do spodní poloviny obrazovky, tap targety min. 44px, minimální psaní.

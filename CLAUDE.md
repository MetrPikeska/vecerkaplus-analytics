# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.


## Project-Specific Guidelines

This is a Python/Streamlit analytics dashboard for VečerkaPlus (night delivery service). It is separate from the main React/Vercel app and runs on its own Ubuntu server at `data.vecerkaplus.cz`.

### Running the app

```bash
pip install -r requirements.txt
cp .env.example .env  # fill SUPABASE_URL and SUPABASE_SERVICE_KEY
streamlit run app/Home.py --server.port 8501
```

There are no tests. Verify changes by running the app and exercising the relevant page.

### Architecture

```
app/Home.py             — dashboard + live order monitoring (auto-refresh via time.sleep + st.rerun)
app/pages/1_Produkty.py — product catalog with photos
app/pages/2_Marze_a_Cenik.py — margin analysis with Makro CSV upload + fuzzy matching
app/pages/3_Objednavky.py    — order analytics (heatmap, market basket via Apriori)
app/pages/4_Rozvoz.py        — delivery cost calculator (Google Distance Matrix)
src/config.py           — env vars + constants (TARGET_MARGIN, FUZZY_CUTOFF, TIMEZONE, ORIGIN)
src/supabase_client.py  — singleton Supabase client
src/etl/load.py         — raw DB fetches (products, orders)
src/etl/clean.py        — type casting, timezone normalization
src/etl/transform.py    — explode_items(), hourly_heatmap(), top_products(), daily_revenue()
src/etl/demo_data.py    — synthetic order generator (150 orders) for the demo toggle
data/distance_cache.json — persisted Google Maps distance cache
```

Pages import from `src/` using `sys.path.insert(0, ...)` at the top — all pages do this.

### Key data facts

- Supabase requires **SERVICE ROLE KEY** — anon key has RLS blocking SELECT on `orders`
- `orders.items` is a JSONB column: `[{"id": "uuid", "name": "...", "price": 59, "quantity": 2}]`
- Order statuses: `nová → přijatá → doručená`, cancellable to `zrušená` from any state
- Timezone: always `Europe/Prague` — use `pytz.timezone(TIMEZONE)` from `src.config`
- Revenue KPIs count only orders with `status == "doručená"`
- Demo data uses real product names/prices; toggled per-page via `st.session_state`

### Context

Read `CONTEXT.md` for domain terminology and business rules. Read `VISION.md` for roadmap phases — focus on Phase 1 (current) only.

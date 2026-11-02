# Corvana knowledge layer

A small, working knowledge layer for one question, *"If the Republic of Corvana is downgraded, what in my book is
exposed, how, and what does our research say about it?"*, and the typed tools an agent uses to answer it with every
fact traced to its source and filtered by the asking user's entitlements.

- `narrative.md` – the write-up (model, identities and conflicts, deterministic vs LLM, measurement, next steps) and the dated log of design decisions
- `TODO.md` – open work after the proof of concept and the known issues found in testing
- `model/` – the model: `schema.dbml` (the model as code, source of the generated DDL), `ground_truth.md` (what the answer needs, ingest rules, tool contract), `table_review.md` (every table and column with its verdict)
- `src/kl/db/` – `010_tables.sql` (generated from the DBML by `kl-schema`, never edited), `020_logic.sql` (views,
  functions: alias, edges, precedence, quality, research ranking, path finder), `030_security.sql` (row-level security)
- `CLAUDE.md` – what to trust in this repo and how work is split
- `src/kl/curation/` – aliases, countries, predicates, rating scale, desk-note label, hand-extracted statements with verbatim quotes
- `tests/expected/` – hand-written expected answers; `tests/` – runnable versions
- `transcripts/` – tool-call transcripts for alice and bob, the point-in-time question, the annotation run and the 2026-10-28 update (see `transcripts/README.md`)
- `ai_tooling_notes.md` – how AI coding tools were used

## Run it

Requirements: PostgreSQL running locally (tested with 18) with a password for `postgres` in `%APPDATA%\postgresql\pgpass.conf`
or `PGPASSWORD`; [uv](https://docs.astral.sh/uv/). For the LLM steps (annotation, update extraction, agent) copy
`.env.example` to `.env` and paste an `ANTHROPIC_API_KEY`; `.env` is gitignored and read by `config.py` at start.
Everything else runs without it.

```powershell
uv sync --group dev
uv run kl-schema                             # regenerate src/kl/db/010_tables.sql from model/schema.dbml
uv run kl-load                               # drop/create database corvana_kl, roles, load the pack, print counts (no LLM)
uv run kl-validate                           # consistency checks; exit 0 when clean
uv run pytest -q                             # expected answers against the database
uv run pytest -q -m stress                   # ingest stress test: builds a scratch database, 13 synthetic deliveries (~20 s)

uv run kl-demo --user bob                    # optional: scripted tool calls, no LLM (offline fallback)

uv run kl-annotate --all                     # Sonnet, grounded in the alias scan: about_*, topics, summary per document (needs the key); --missing, --document <id>
                                             # --extract runs the EXPERIMENTAL relationship extractor as well (off by default)
uv run kl-agent --user alice                 # Opus over the same tools; writes transcripts/agent_alice_*.md
uv run kl-agent --user bob
uv run kl-agent --user bob   --question "What was the state's stake in Corvana Power & Light on 2025-06-30, and what is it now?"
uv run kl-agent --user alice --question "What was the state's stake in Corvana Power & Light on 2025-06-30, and what is it now?"

uv run kl-update data/updates/2026-10-28     # Part 3: apply / discard / flag; annotate the new note (no extraction); writes transcripts/update_2026-10-28.md
uv run kl-agent --user bob --as-of 2026-10-28 --question "Corvana was downgraded to B+ yesterday. What in my book is exposed, how, and what does our research say about it?"
uv run kl-validate; uv run pytest -q
uv run kl-update data/updates/2026-10-28     # second run: no-op

uv run kl-mcp                                # MCP server over stdio exposing the eight tools
```

Environment overrides: `KL_PG_DB`, `KL_PG_ADMIN`, `PGHOST`, `PGPORT`, `KL_AS_OF` (default 2026-10-27), `KL_MODEL`
(agent, default `claude-opus-5-5`), `KL_ANNOTATE_MODEL` (annotation, default `claude-sonnet-5-5`), `KL_ANNOTATE_MIN_CONFIDENCE` (default 0.5),
`KL_PACK_DIR`.

## Modules (`src/kl/`)

| module | job |
|---|---|
| `config.py` | paths, DSN, `AS_OF`, model ids, `.env` loading |
| `schema_gen.py` | `kl-schema`: `model/schema.dbml` → `db/010_tables.sql` (pydbml) |
| `db/` | generated tables; hand-written logic (alias, source_tier, position_resolved, rating_current, edges, current_statements, link_quality, data_quality with the nearest-match hint, hidden_newer_count, research_for_paths, exposure_paths); row-level security |
| `curation/` | aliases, countries, predicate definitions, rating scale, desk-note label, hand-extracted statements |
| `load.py`, `resolve.py` | pack → Postgres; name resolution through the `alias` view; alias-scan annotation of documents; rule statements |
| `validate.py` | self-checks (schema matches DBML, alias uniqueness, unresolved names, quotes, labels, roles, annotation), non-zero exit on failure |
| `tools.py` | the eight typed tools, summary first; `mcp_server.py` exposes them over MCP |
| `demo.py` | scripted tool calls, no LLM; `agent.py` Claude tool-runner over the same tools |
| `extract.py` | `kl-annotate`: one grounded LLM call per document (each alias-scan mention with context and candidates → chosen id + confidence; added mentions must quote the text; topics, summary). Relationship extraction kept as an experiment behind `--extract` |
| `ingest_update.py` | `kl-update`: Part 3 apply / discard / flag, grounded annotation of the delta's documents (no extraction) |
| `tests/` | runnable expected answers, direct SQL per view, schema generation, ingest rules, extractor checks, summary-first tool shapes, MCP smoke, update |

## Shape in one paragraph

Level 1: one table per file in the pack, as delivered minus columns nothing reads, plus a curated `aliases[]`
column and ids resolved at load (`issuer_id`, `guarantor_id`, `owner_id`, `owned_id`, `ratings.issuer_id`) with the
raw name kept beside each id. Level 2: `statements`, the links no file column holds (rule rows INFERRED, document
rows PROPOSED) with `as_of`, source, quote, visibility and status; the `edges` view unions them with the level-1
links so the graph is one thing, `current_statements` picks the current value per link by a deterministic trust rule
and `data_quality` names every disagreement. Level 3: one `documents` table with text, label and what each document
is about (`about_*` ids, topics, summary) written by an alias scan at load and, where a key exists, by the LLM
grounded in that scan (it chooses among the scan's candidates and may add a mention it can quote; it never removes an
unambiguous match). The LLM identifies entities only; relationships come from rules and hand curation.
Postgres roles and row-level security decide what each user sees; the tools `SET ROLE` to the asking user, so alice
and bob get different answers from the same query.

## Tools (also exposed over MCP)

`find_entity`, `get_positions`, `get_exposure`, `get_path`, `get_statements`, `get_documents`, `get_document`,
`get_ratings`. Every tool takes the asking user and an optional as-of date, and every cited fact carries a statement
id or a level-1 edge id (e.g. `instruments:INS-1004:issuer_id`), source, as-of date, quote and status.

Summary first. `get_exposure` returns, by default, per resolved position the verdict (yes / unconfirmed / no), the
channels with grade, hop count and one edge id per hop, and the flag kinds; the holdings the layer could not
identify in their own `unresolved` block (amount and the UNRESOLVED_REF message, which names a known identifier one
edit away when there is one and says it was not applied); and the research about the entities on the paths, ranked
in SQL by `research_for_paths` (path entities matched, then newest; capped by `max_documents`, default 10) with a
one-line summary each and no text. `detail='full'` gives every citation and the documents' text. The drill-downs
are `get_path` (one channel, every citation, paths considered) and `get_document` (one document with its text; a
document the user may not read raises an error, indistinguishable from a missing one). `get_documents` returns
summaries unless `text=True`. A document's summary and topics are pointers to the document, never citations; the
citation is the document id and its text.

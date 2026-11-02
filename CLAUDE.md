# CLAUDE.md – where things are and what to trust

Take-home for a knowledge-engineer role (`BRIEF.md`). One question drives everything: *"If the Republic of Corvana
is downgraded, what in my book is exposed, how, and what does our research say about it?"* The data pack under
`data/` is fictional and read-only. Today is 2026-10-27 for the data; the delta in `data/updates/2026-10-28/` is
Part 3.

This file is an overview and a map; it does not repeat what the files below say. When a detail here and a detail
there differ, the file it points to wins.

## 1. Truth (read these first)

| file | what it is |
|---|---|
| `BRIEF.md` | the task. Never edit. |
| `model/ground_truth.md` | what the answer needs: entities, columns, links, documents, the ingest rules (section 12) and the tool contract (section 13), derived from the question. The model is tested against this. |
| `model/table_review.md` | every table and column with a keep/drop verdict and the reason. Its closing table is the target state. |
| `model/schema.dbml` | the model as code: tables and relationships inline, grouped data/metadata, with the derived views and functions listed at the end. `src/kl/db/010_tables.sql` is generated from it by `kl-schema` and never edited by hand; views, functions and security are hand-written SQL in `020_logic.sql` and `030_security.sql`. |
| `tests/expected/*.md` | hand-written expected answers per user and question. The contract the tests run. Edit only when `ground_truth.md` changes, never to make a test pass. |
| `data/` | the pack, as delivered. Never edit, never write into. |
| `narrative.md` | the Part 4 write-up in the author's voice: sections 1–5 answer the brief. Owned by the author; do not append logs to it. |
| `ai_tooling_notes.md` | the brief's note on AI tooling: how the sessions were used, what was changed or rejected and why, key prompts. |
| `TODO.md` | open work after the proof of concept, in order, and the known issues found in testing. Add to it; do not fix silently. |

## 2. Principles (do not re-litigate; details and exceptions are in the files above)

1. **Three levels.** Source tables as delivered, links with provenance, documents. The levels, their tables and
   the recorded exceptions are defined in `model/schema.dbml` and explained in `model/table_review.md`.
2. **Never merge sources.** A newer value is a new row. Precedence and quality are views. Nothing is overwritten.
3. **Trust rule.** A person's confirmation first, then file values and rules, then research; a research row can flag
   and is returned beside the winner. The definition is in the schema's `statements` note and in `020_logic.sql`.
4. **Entitlements live in Postgres.** Roles per user, book and label; row-level security; tools `SET ROLE` to the
   asking user. The agent never filters.
5. **Only what the ground truth needs.** A column or table earns its place by appearing in `ground_truth.md`,
   except the audit columns kept on every table.
6. **Denormalised columns over join tables** when the row is what gets looked up. Plain typed columns over jsonb.
7. **LLM in two places only**, both validated against reference data: grounded annotation of documents (entities,
   topics, summary; relationship extraction is an experiment behind a flag) and the agent over the tools. The base
   pack's statements are hand-curated. Everything must run without an API key except the LLM steps themselves.
8. **Report, don't fix.** If the data or the expected answers look wrong, say so; do not edit an expectation to
   make a test pass. Table changes go into the DBML and are regenerated, never into the SQL; any change to the
   hand-written SQL files is reported explicitly.

## 3. Code

`src/kl/` implements the model above and passes its suite (`uv run pytest -q`) and validator (`uv run kl-validate`).
Module roles and run commands are in `README.md`; `scripts/` holds the two LLM measurements. Environment:
PostgreSQL 18 local, `psql` at `C:\Program Files\PostgreSQL\18\bin`, `uv` with `[tool.uv] system-certs = true`,
Python 3.12 pinned. The Anthropic key lives in the gitignored `.env` (see `.env.example`); never print or log it.

## 4. History

The repo went through three designs before the 2026-10-31 rework to the lean model; the earlier design documents
were deleted. The decisions and the disagreements with the AI tooling are summarised in `ai_tooling_notes.md`. `transcripts/` holds only output of the
current code (`transcripts/README.md` says what each file is).

## 5. How work is split

A design session (Fable) owns `model/`, `tests/expected/`, `narrative.md`, `ai_tooling_notes.md`, `TODO.md` and
reviews. Delimited implementation (schema generation, loader, tools, tests, ingest) is delegated to
a Claude Code session named `opus_implement` with a brief that names the files it owns, the expected counts after
load, and the expected files as the contract. Any agent working here follows the same split: if a task is "make the
code match `model/`", it is implementation.

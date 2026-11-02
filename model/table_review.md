# Table-by-table review against `ground_truth.md`

Rule applied to every column: keep it if the ground truth uses it to answer, resolve, order, or cite. Prefer a
denormalised column on the row that is looked up over a join table. Resolve free-text names to ids at load and keep
the raw text beside the id as evidence. Date columns: `updated_on` on every table is when the layer wrote the row
(audit); a file's own date keeps the file's name (`last_updated`, `as_of_date`, `action_date`, `published_at`);
`statements.as_of` is when a link was true. Keep two
audit columns per table regardless: a source (`source_system` and/or `source_file`) and `updated_on`. Everything
else goes. Nineteen tables reviewed; thirteen stay, six go (three of them folded into other tables or a view).

Legend: **keep** / **drop** / **merge**.

## Level 1: source tables

### sources (keep, 3 columns dropped)

| column | verdict | reason |
|---|---|---|
| source_id | keep | FK target; the citation's system |
| description | keep | the citation text ("Security master") |
| reliability | keep | the owner's words; `source_tier` maps them to 3/2/1, which drives precedence |
| owner | drop | not cited, not used |
| files | drop | only a validator could use it; none does |
| source_file, updated_on | keep | audit |

### entitlements (keep, 1 column dropped)

| column | verdict | reason |
|---|---|---|
| username, books, research_visibility | keep | roles and RLS are generated from them |
| role | drop | a job title; not an entitlement |
| source_file, updated_on | keep | audit |

### country (keep, curated)

| column | verdict | reason |
|---|---|---|
| code | keep | key |
| name | keep | the alias "Corvana" for the country and the name in the answer |
| aliases | add | curated other names |
| currency | keep | CURRENCY_OF hop (CVD → QC) |
| sovereign_issuer_id | keep | SOVEREIGN_IS hop (QC → ISS-0001) |
| updated_on | keep | audit; source is the curation file by definition |

### rating_agency (drop, merge into rating_scale)

One agency. The agency name is a column of `rating_scale` and of `ratings`; a table with one row and one column
is a FK target and nothing else. The 'agency' alias rows go.

### rating_scale (keep, 1 column dropped)

| column | verdict | reason |
|---|---|---|
| agency, rating, rank | keep | rank comparison for RATING_LAG and "one notch above sovereign" |
| investment_grade | drop | not asked |
| updated_on | keep | audit |

### issuers (keep, 3 columns dropped)

| column | verdict | reason |
|---|---|---|
| issuer_id, legal_name, short_name | keep | identity and the two file-supplied aliases |
| aliases | add | curated other names, `text[]`, GIN index (see alias below) |
| country_of_incorporation | keep | COUNTRY_OF_RISK rule |
| last_updated | keep | as_of of inferred rows |
| lei | drop | nothing in the pack refers by LEI. First column back at firm scale |
| issuer_type | drop | "Sovereign" is not read; the country → sovereign link is curated |
| sector | drop | on no path, in no citation |
| source_system, source_file, updated_on | keep | audit |

### curves (keep, 1 column dropped)

| column | verdict | reason |
|---|---|---|
| curve_id, description, currency | keep | PRICED_OFF target; DENOMINATED_IN hop to the currency |
| aliases | add | curated other names ("CVD govt curve") |
| country | drop | duplicates the currency → country hop; a curve in CVD is Corvana's by construction |
| source_system, source_file, updated_on | keep | audit |

### instruments (keep, 2 columns dropped, 2 resolved ids added)

| column | verdict | reason |
|---|---|---|
| instrument_id, isin, ticker | keep | resolution by ref_type |
| description, instrument_type | keep | naming; CDS → REFERENCES_CREDIT |
| aliases | add | curated other names ("CDB 27s", "3M NDFs") |
| issuer_name, guarantor_name | keep, raw | the text as SecMaster wrote it: the evidence for the resolution and the quote on the edge; a name that resolves to nothing is an UNRESOLVED_NAME flag with text to show |
| issuer_id, guarantor_id | add | resolved at load through the alias view (by name, not ticker: CNOC Finance's bonds carry the parent's ticker). FK to issuers. ISSUED_BY / REFERENCES_CREDIT / GUARANTEED_BY become level-1 edges |
| currency, underlying_curve | keep | the two level-1 channels |
| coupon, maturity | drop | size and tenor are not the question |
| source_system, source_file, updated_on | keep | audit |

### ownership (keep, as delivered, 2 resolved ids added)

Every file column is used: owner and owned_entity (as written, evidence), stake_pct (the value), as_of_date (the
date the PIT question turns on), source (the tracker's own citation), notes (two rules read it: the CDB guarantee,
the CNOC Finance vehicle). Added: owner_id and owned_id, resolved at load, FK to issuers. The row is then an OWNS
edge in its own right (owner_id → owned_id, value stake_pct, as_of as_of_date, tier 2) and is no longer copied into
statements. Plus source_file, updated_on. The surrogate key stays because the file has none.

### ratings (keep, as delivered, 1 resolved id added)

entity (as written, evidence), agency, rating, outlook, action_date, source → all used. Added: issuer_id, resolved
at load, FK to issuers, so `rating_current` is a plain query and the `ratings_resolved` view goes. The FK to
rating_scale stays so a rating outside the scale cannot load. Plus source_file, updated_on.

### positions (keep, as delivered)

All six file columns used; plus source_file, updated_on.

## Level 2: links

### alias (drop as a table; becomes a column and a view)

Curated names move onto the entity they name: `aliases text[]` on `issuers`, `instruments`, `curves`, `country`,
holding only the names that are not already a column of the row (the legal name, short name, ticker, ISIN and
country name are aliases by being there). Resolution still has one entry point: an `alias` view that unions every
name column and array element into `(entity_type, entity_id, alias)`. The loader, extractor and annotator query the
view exactly as they queried the table.

This is a recorded compromise. Against it: a level-1 table now carries a column
written from the curation source, not from the file; an array column cannot hold a unique index across its
elements, so "one name resolves to one entity" moves into `validate.py`; matching inside arrays is a scan per row,
which is free at ten issuers and slow at a million, and limits what SQL can do with a name (no foreign key from a
name, no join on it without `unnest`). For it: one table less, and an entity row says what the entity is called,
which is how a person reads it. "Where the name was seen" stays in `curation/aliases.yaml`.

### predicate_def (keep, one row dropped)

The model as code: predicate, single_valued, compare, direction, description. EXPOSED_TO goes (no path uses it).
HAS_VIEW goes (see statements). Fourteen predicates remain.

### statements (keep, 3 columns dropped)

| column | verdict | reason |
|---|---|---|
| statement_id | keep | the citation id |
| (what a row is) | narrowed | a link that no file column holds: from a rule or a document. Links held by a column (issuer_id, guarantor_id, owner_id → owned_id, currency, curve, country → sovereign) are projected by `edges`, not stored twice |
| subject_type, subject_id, predicate, object_type, object_id | keep | the link |
| value_num | keep | stake, beta, correlation |
| value_text | keep | OWNS qualifiers ("indirect via holding") |
| value_kind | drop | only HAS_VIEW used it |
| holds | keep | denials (CorTel 2023, Valdoria) |
| as_of | keep | point in time |
| source_system | keep | tier for precedence; citation |
| source_file | keep | audit; which file or document |
| document_id | keep | citation into the document; RLS via visibility |
| quote | keep | the verbatim sentence or the rule text |
| method | keep | RULE / MANUAL / LLM: how the row came to exist. FILE goes: a file value is an edge, not a statement |
| checked | drop | derivable: MANUAL rows were checked by a person, LLM rows by the auto-check, FILE/RULE rows by the loader. Nothing reads it |
| status | keep | INFERRED / PROPOSED / CONFIRMED / REJECTED drives precedence. REFERENCE appears only on level-1 edges in the `edges` view |
| visibility | keep | denormalised from the document on purpose: the RLS policy must not join |
| updated_on | keep | audit |

**HAS_VIEW rows go (20 of 73).** They are opinions, not links; they never move a path. The "what does research
say" half of the question is answered by returning the visible documents that are about an entity on the path
(the `about_*` columns below) and letting the agent quote the text. Keeping a parallel table of hand-copied opinions
doubles the curation and adds a second place a quote can be wrong. The statement table then holds exactly what the
name says: a relationship between two things, from a source, at a date.

Consequence for the tools: `get_statements` no longer returns `views`; `get_documents(entity_id)` is the way to
read research, and it reads the `about_*` columns instead of a mentions join. The "matter at hand" of a note is its
summary and topics on one row, not twenty hand-copied opinion statements. `tools.py`, `demo.py`, `agent.py` prompt, `statements.yaml` (20 rows), `extract.py` schema and
`tests/expected/alice_exposure.md` (one line) change.

## Level 3: documents

### documents (keep, widened with the annotation columns)

Research notes and desk-chat lines share this table by decision (recorded in `narrative.md`): similar content,
one shape, `kind` and `source_system` keep them distinguishable. The alternative, one table each, was considered
and deferred.

document_id, source_file, kind, title, publisher, author, published_at, visibility, text, updated_on stay. Added,
all on the same row:

| column | type | written by | reason |
|---|---|---|---|
| about_issuers | text[] | annotator | "research about ISS-0003" is `where 'ISS-0003' = any(about_issuers)`; GIN index |
| about_instruments | text[] | annotator | same, for holdings named directly ("CVGB 2033", "3M NDFs") |
| about_curves, about_currencies | text[] | annotator | the macro note is about CVD and the CVD govt curve |
| topics | text[] | annotator | downgrade, guarantee, ownership, FX, ... : lets the agent pick documents before reading them |
| summary | text | LLM only | one line; a pointer to the document, not a citation |
| annotated_by | text | loader | RULE (alias scan) or LLM. Says which annotator wrote the about_* columns |

Two annotators fill the same columns. The alias scan runs at load for every document, needs no API key and is
repeatable. The LLM annotator runs where a key exists, must resolve every entity it names through `alias` (else the
entity is dropped and reported), and overwrites the scan's columns, adding summary and topics. Level 3 is one table.

### document_mentions (drop, folded into documents)

Its content becomes the `about_*` arrays. What is lost is per-mention detail (which word matched, which method
found it); the answer never used it, and re-annotating one document is how a missed mention is debugged.

### extraction_review (drop)

Failed LLM output is reported in the ingest transcript, not stored. The brief accepts a report. When a review
workflow exists this table comes back as its queue; `test_extract.py` changes to assert on the returned rejects.

## Bookkeeping

### ingest_log (drop)

The ingest report is `transcripts/update_<date>.md`. Idempotency does not need the log: a rerun finds the rows
already present by their natural keys.

### pending_changes (drop)

The PROPOSE branch for a changed level-1 row is design only (no delta exercises it). The write-up describes it;
the schema does not carry an empty table for it.

## Groups

`model/schema.dbml` separates data from metadata with table groups: **metadata** (sources, entitlements,
predicate_def: configuration the layer runs on, never cited in an answer), **reference_curated** (country,
rating_scale), **level1_source_data** (issuers, curves, instruments, ownership, ratings, positions), **level2_links**
(statements), **level3_documents** (documents).

## Schema files

`src/kl/db/010_tables.sql` is generated from `model/schema.dbml` by `kl-schema` (pydbml) and never edited by hand;
a test fails when the committed file differs from a fresh generation. `020_logic.sql` (views and functions, plus
the two GIN indexes) and `030_security.sql` (roles template and row-level security) are hand-written and contain no
table definitions. All logic stays in SQL for now (decision recorded in `narrative.md`). `020_logic.sql` enables the `fuzzystrmatch`
extension (shipped with Postgres) for the edit-distance hint on unresolved position refs.

## Views and functions

| object | verdict | reason |
|---|---|---|
| alias (view) | add | union of every name column and `aliases[]` element; the single resolution lookup |
| source_tier | keep | precedence |
| position_resolved | keep | resolution by ref_type |
| ratings_resolved | drop | ratings.issuer_id is now a column |
| rating_current | keep | latest rating per issuer; RATING_LAG |
| edges | keep, widened | statements ∪ every level-1 link (issuer, guarantor, owner → owned, currency, curve, country → sovereign) with the raw name as quote and REFERENCE or INFERRED by whether an alias did the work; the graph |
| current_statements(as_of) | keep, over edges | precedence per date across statements and level-1 edges, so the tracker's 51 and the IPO note's 34 still compete on one link |
| link_quality(as_of) | keep | CORROBORATED / STALE / CONFLICT / SUPERSEDED |
| data_quality | keep | plus UNRESOLVED_REF, UNRESOLVED_NAME (a level-1 name column that resolved to no id), UNLABELLED_DOCUMENT, UNKNOWN_LABEL, UNKNOWN_BOOK, RATING_LAG |
| hidden_newer_count | keep | the "newer information exists" count for alice |
| exposure_paths | keep | the path finder |
| issuer_current | drop | a convenience for humans, read by nothing; it is the flat-column design the model moved away from |

## Net effect

| | before | after |
|---|---|---|
| tables | 19 | 13 |
| predicates | 16 | 14 |
| statements at load | 73 | 33 (10 country-of-risk rules, 2 from ownership.notes, 21 curated) |
| curated statements | 43 | 21 |
| columns dropped from kept tables | | 12 |
| columns added | | aliases[] on four tables; issuer_id and guarantor_id on instruments; owner_id and owned_id on ownership; issuer_id on ratings; seven annotation columns on documents |

"Before" is the design this review replaced; "after" is the current `model/schema.dbml` and the code under `src/kl/`.

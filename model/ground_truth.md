# Ground truth: what the layer must contain to answer the PM's question

Question: *"If the Republic of Corvana is downgraded, what in my book is exposed, how, and what does our research say
about it?"* Asked by alice and by bob, as of 2026-10-27, plus the point-in-time question on CPL and the 2026-10-28
delta. This file is the inventory the model is tested against. Anything not listed here is out of scope for the
schema. `tests/expected/*.md` are the per-user renderings of this inventory; `tests/test_questions.py` runs them.

## 1. The question, decomposed

| part of the question | what has to exist | how it is answered |
|---|---|---|
| "in my book" | the asking user, their books, the positions in those books | entitlement → positions filtered by book |
| "what is exposed" | each position resolved to an instrument, and a path from that instrument to ISS-0001 | position ref → instrument; path over links |
| "how" | the links on the path, each with its source, date, status and whether it is reference-grade | statements and level-1 joins, with provenance |
| "what does our research say" | the documents the user may read that are about an entity on a path, with their text | documents with about_* columns and visibility |
| "with sources cited" | every link and every document carries source file, date, quote | provenance columns |
| point in time | every link has a business date and an arrival date; nothing is overwritten | "as known at": business date <= as_of and updated_on <= as_of; precedence picks per date |
| the delta | new instrument, new rating events, new document; links extracted from it | same tables, append only |

## 2. Users and books

| user | books | research labels |
|---|---|---|
| alice | EM_MACRO | external, macro_internal |
| bob | EM_CREDIT | external, credit_internal |
| carol | EM_MACRO, EM_CREDIT | external, macro_internal, credit_internal |

Needed: username, books, labels. Not needed: the job title.

## 3. Positions (14 rows, all needed)

Every column of the OMS file is used: book (entitlement), instrument_ref and ref_type (resolution), quantity and
notional_ccy (the "what"), as_of_date (point in time). Positions are not given a resolved id column: the OMS
ref is already an identifier of a declared kind, and `position_resolved` joins it; an unmatched ref is an
UNRESOLVED_REF flag, never a guess. The positions of a book are read at that book's latest as_of_date on or before
the as-of date, so a delivery for one book never hides another. A resolved instrument whose issuer did not resolve
is an unresolved holding (UNRESOLVED_NAME), never "not exposed".

| book | ref | ref_type | resolves to |
|---|---|---|---|
| EM_MACRO | XS2812345671 | ISIN | INS-1001 |
| EM_MACRO | QC000CV33031 | ISIN | INS-1004 |
| EM_MACRO | INS-2002 | INTERNAL | INS-2002 |
| EM_MACRO | CVD IRS 5Y | TICKER | INS-2003 |
| EM_MACRO | XS2900123451 | ISIN | INS-1010 |
| EM_MACRO | GB00NB123454 | ISIN | INS-1011 |
| EM_CREDIT | XS2812345672 | ISIN | nothing (reported, not guessed) |
| EM_CREDIT | CNOC 5.875 11/04/29 | TICKER | INS-1005 |
| EM_CREDIT | XS2500445569 | ISIN | INS-1006 |
| EM_CREDIT | INS-1007 | INTERNAL | INS-1007 |
| EM_CREDIT | XS2700334415 | ISIN | INS-1008 |
| EM_CREDIT | XS2300665523 | ISIN | INS-1009 |
| EM_CREDIT | INS-2001 | INTERNAL | INS-2001 |
| EM_CREDIT | XS2999887768 | ISIN | nothing until the delta adds INS-1012 |

## 4. Instruments: which columns the answer touches

| column | needed | used for |
|---|---|---|
| instrument_id, isin, ticker | yes | position resolution by ref_type |
| description | yes | naming the holding in the answer |
| aliases (curated) | yes | names documents use for a holding: "CDB 27s", "3M NDFs", "CVD 5Y swaps", "CVGB 2033" |
| instrument_type | yes | CDS → REFERENCES_CREDIT instead of ISSUED_BY; labelling |
| issuer_name, guarantor_name | yes, as written | the evidence: what SecMaster called the issuer ("Corvana Ministry of Finance" for a Republic bond) |
| issuer_id, guarantor_id | yes, resolved at load | the ids the paths use; ISSUED_BY, REFERENCES_CREDIT (CDS) and GUARANTEED_BY are read from these columns |
| currency | yes | DENOMINATED_IN channel (CVD → QC → sovereign) |
| underlying_curve | yes | PRICED_OFF channel (CVD-GOVT, CVD-OIS) |
| coupon, maturity | no | the question asks for the channel, not the size or the tenor |

Instruments on a path to ISS-0001: INS-1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009 (desk only), 1010
(research only), 2001, 2002, 2003, and 1012 after the delta. INS-1011 must exist to be reported as not exposed.

## 5. Issuers: which columns the answer touches

| column | needed | used for |
|---|---|---|
| issuer_id, legal_name | yes | identity, the name in the answer, the legal-name alias |
| short_name | yes | one more alias ("CNOC", "CPL", "CDB", "CorTel") |
| aliases (curated) | yes | the other names the pack uses: "Rep. of Corvana", "Corvana Ministry of Finance", "Corvana Power and Light", "Corvana Telecommunications", "Corvana National Oil Co", "CNOC Finance BV"; stored on the issuer row, resolved through the `alias` view |
| country_of_incorporation | yes | the COUNTRY_OF_RISK rule (every QC issuer is exposed as Corvana-domiciled) |
| last_updated | yes | the as_of date of rules derived from the row |
| lei | no | no source in the pack refers to anything by LEI |
| issuer_type | no | "Sovereign" is not used: the country → sovereign link is curated (QC → ISS-0001) |
| sector | no | not on any path, not cited by any research |

Issuers that must exist: ISS-0001 (target), 0002, 0003, 0004, 0005, 0007, 0008, 0009 (on paths), 0010 (not
exposed). ISS-0006 First Corvana Bank is in the pack and in no book; it is loaded because the file is loaded, and
nothing in the answer depends on it.

## 6. Curves, countries, currencies

| entity | needed | why |
|---|---|---|
| curves CVD-GOVT, CVD-OIS | yes | the rates-curve channel for INS-1003, 1004, 2003. The brief names "its rates curve". Columns: curve_id, description, currency. The file's `country` column duplicates the currency → country hop and is not needed. |
| curve USD-SOFR | loaded, unused | leads to US, not to the target |
| country QC → currency CVD → sovereign ISS-0001 | yes, curated | the currency and curve channels end here. Columns: code, name, currency, sovereign_issuer_id |
| countries GB, NL, US, QV | yes | so that incorporation resolves; none leads to the target (QV → ISS-0009 is used by the Valdoria correlation path start, not as a channel) |
| currency as an entity | implicit | a currency is a code on instruments, curves and country; no table of its own |

## 7. Links needed, with the source that supplies each

Reference-grade. Level-1 edges are read straight from a resolved column and projected by the `edges` view (REFERENCE
when the raw name was the legal name, INFERRED when an alias resolved it); rule rows are INFERRED statements:

| predicate | from → to | source | kind |
|---|---|---|---|
| ISSUED_BY | 11 bonds → their issuers | instruments.issuer_id (resolved at load from issuer_name: legal name for 6, alias for 5: "Rep. of Corvana", "Corvana Ministry of Finance", "Corvana Power and Light", "Corvana Telecommunications") | level-1 edge |
| REFERENCES_CREDIT | INS-2001 → ISS-0001 | instruments.issuer_id where instrument_type = CDS | level-1 edge |
| GUARANTEED_BY | INS-1007 → ISS-0001; INS-1005 → ISS-0002 | instruments.guarantor_id (legal name; alias "Corvana National Oil Co") | level-1 edge |
| OWNS | ISS-0001 → 0002 (100), 0004 (100), 0003 (51); ISS-0002 → 0007 (100) | ownership.owner_id → owned_id, value stake_pct, as_of as_of_date | level-1 edge, tier 2 |
| GUARANTEED_BY | ISS-0004 → ISS-0001 | ownership.notes "Explicit sovereign guarantee on senior debt" | INFERRED statement |
| FINANCING_VEHICLE_OF | ISS-0007 → ISS-0002 | ownership.notes "Financing vehicle" | INFERRED statement |
| COUNTRY_OF_RISK | every issuer → its country of incorporation; ISS-0007 → QC (vehicle takes the parent's) | rule | INFERRED statement |
| DENOMINATED_IN | instrument → currency; curve → currency | instruments.currency, curves.currency | level-1 edge |
| PRICED_OFF | instrument → curve | instruments.underlying_curve | level-1 edge |
| CURRENCY_OF, SOVEREIGN_IS | CVD → QC → ISS-0001 | country.currency, country.sovereign_issuer_id | level-1 edge |

Precedence runs over edges and statements together, so the tracker's 51 (edge) and the IPO note's 34 (statement)
compete on the same link.

Research and desk only (PROPOSED; never current when a reference-grade row exists on the same link; otherwise
current but labelled unconfirmed):

| predicate | from → to | document | role in the answer |
|---|---|---|---|
| OWNS | ISS-0001 → ISS-0003 = 34 (2026-02-24) | CPL IPO note, credit_internal | flags the tracker's 51 as STALE for bob; hidden count for alice; the PIT question |
| OWNS | ISS-0001 → ISS-0003 = 51 | Bank A 2024-05-14 | corroborates the tracker on 2025-06-30 |
| OWNS | unresolved strategic investor → ISS-0003 = 25 | CPL IPO note | other source, no path |
| OWNS | ISS-0001 → ISS-0005 = 20 (desk 2026-02-11), 35 indirect (Bank A 2023) | desk, Bank A | CorTel's only ownership rows; the delta corroborates 20 |
| OWNS | ISS-0001 → ISS-0002 = 100 | Bank A 2024, Bank A 2026 | corroborate the tracker |
| GUARANTEED_BY | ISS-0004 → ISS-0001 | Bank A 2024, Bank B 2026-09-22, desk 2026-09-19 | corroborate the tracker note |
| GUARANTEED_BY | ISS-0007 → ISS-0002 | Bank A 2026-06-10 | issuer-level guarantee behind INS-1005 |
| FINANCING_VEHICLE_OF | ISS-0007 → ISS-0002 | Bank A 2026-06-10 | corroborates ownership.notes |
| RATING_CAPPED_BY | ISS-0002 → ISS-0001 | Bank B 2026-09-22 | the CNOC channel; explains the CNOC downgrade in the delta |
| TRADES_AS_PROXY_FOR | ISS-0002 → 0001 (Bank A 2024); ISS-0005 → 0001 holds=false (Bank A 2023) then true (desk 2026-02-11, Bank B 2026-10-28); ISS-0009 → 0001 holds=false (Bank B 2025) | research, desk | the CorTel supersession; the Valdoria denial |
| BETA_TO | ISS-0003 → ISS-0001 = 0.6 | CPL IPO note | the CPL channel bob sees and alice does not |
| CORRELATED_WITH | ISS-0009 → ISS-0001 = 0.7 | Bank B 2025-11-18 | alice's Valdoria "research only" channel |
| COUNTRY_OF_RISK | ISS-0008 → QC | desk 2026-04-30 | Meridian: CONFLICT with the GB rule row; "desk view only" |

Not needed: EXPOSED_TO (First Corvana Bank holds sovereign paper; no position reaches the target through FCB).
HAS_VIEW rows (recommendations, forecasts, assessments) are not links. The answer needs the sentence and the
document, which the `documents` row (text, summary, topics, about_*) already gives; a separate opinion row
duplicates the text.

## 8. Documents (9 in the pack, 1 in the delta)

| file | label | why the answer needs it |
|---|---|---|
| 2023-10-02 Bank A CorTel initiation | external | CorTel standalone (later superseded), 35% indirect |
| 2024-05-14 Bank A sovereign outlook | external | CNOC 100%, CDB guarantee, CPL 51%, CNOC proxy |
| 2025-11-18 Bank B Valdoria spillovers | external | correlation 0.7, proxy denied |
| 2026-03-05 internal CPL IPO | credit_internal | 34%, beta 0.6; must not reach alice |
| 2026-06-10 Bank A CNOC update | external | vehicle, parent guarantee, 100% MinFin |
| 2026-07-01 Bank A UK retail | external | Northbridge: not on a path; shows "not exposed" has research too |
| 2026-08-21 macro internal CVD reserves | macro_internal | views on CVGB 2033, NDFs, swaps; must not reach bob |
| 2026-09-22 Bank B negative watch | external | rating cap, CDB guarantee, buy 5Y protection |
| desk notes, one row per line | credit_internal (assumption) | CorTel 20% and proxy, Meridian QC, CDB "treat like sovereign" |
| 2026-10-28 Bank B downgrade (delta) | external | CorTel 20% corroborated, proxy, CDB guarantee |

Columns needed: source_system, source_file, kind, title, publisher, author, published_at, visibility, text, and on the same row
what the document is about: `about_issuers`, `about_instruments`, `about_curves`, `about_currencies` (arrays of
ids), `topics`, `summary`, `annotated_by`. "Research about an entity on the path" is then a single-table lookup.
The annotation is written by a deterministic alias scan at load (`annotated_by = RULE`) and, where an LLM is
available, replaced by LLM annotation validated against the `alias` view (`annotated_by = LLM`). The summary is a
pointer to the document, never a citation; the citation is the document and its text.

## 9. Ratings

Needed to say "currently BB- / Negative", to show the delta (B+), and to raise RATING_LAG on CDB after it.
Columns: entity (as written), issuer_id (resolved at load), agency, rating, outlook, action_date. The scale (rating →
rank) is needed only for the rank comparison in RATING_LAG and "one notch above". `investment_grade` is not
needed. A separate agency table is not needed: one agency, named in the scale.

## 10. Sources

Needed: source_id and reliability (the tier that drives precedence), and a description for the citation. Not
needed: owner, the file list.

## 11. Explicitly out of scope

Prices, DV01, spread duration, notionals in a common currency; sector and issuer type; LEI; coupon and maturity;
the Ministry of Finance and the central bank as entities distinct from the Republic; the CorTel holding company
and the CPL strategic investor as entities; First Corvana Bank's exposure; opinion rows separate from their
documents; ingest bookkeeping (the report is a transcript file); the review queue for failed extraction (a
rejected extraction is reported, not stored).

## 12. Ingest rules (Part 3) and where a person steps in

| input | rule | action |
|---|---|---|
| level-1 row with a new key, tier-3 or tier-2 source | append | AUTO (INS-1012; two rating events) |
| level-1 row with an existing key and a changed value | a reference-grade source contradicting itself or another | **not applied**: the row is discarded from the load and logged (console and the run report) for a person to decide. A change only in audit columns is skipped; a change in a dropped column is logged once as ignored |
| delta files | dependency order, not filename order: issuers, curves, instruments, ownership, ratings, positions, documents; null ids re-resolved after every batch | |
| document with a label nobody holds, or position in a book nobody holds | stored, logged as FLAG, UNKNOWN_LABEL / UNKNOWN_BOOK in data_quality | |
| re-sent document (same title and text) | skipped, not stored twice | |
| a second reference-grade statement on a link that disagrees with the existing one | same | **not applied**, logged the same way |
| position ref that now resolves | side effect of AUTO | AUTO; "UNRESOLVED_REF closed" in the report |
| document | always safe to store | AUTO into documents, alias-scan annotation; LLM annotation where a key exists |
| statement extracted by the LLM | quote verbatim in the text and both ends resolve | PROPOSED under the document's label; else discarded and logged |
| any new row against existing rows | quality recomputed | STALE / CONFLICT / CORROBORATED / RATING_LAG / UNRESOLVED_NAME reported |

A person is expected at two points, and the layer marks them without implementing the workflow:

1. **Contradictions between high-trust sources.** Discarded at ingest and logged, never applied silently. Also any
   CONFLICT or STALE flag the quality view raises between what is current and a newer or equal-trust row.
2. **Promotion to trusted data.** A document-derived row stays PROPOSED until a person sets it to CONFIRMED (it
   then ranks with REFERENCE) or REJECTED (it drops out of precedence). Today that is a SQL update; the command and
   the audit of who decided are out of scope for this proof of concept.

Logging is to the console and to `transcripts/update_<date>.md`; there is no bookkeeping table.

Rules added after the ingest stress test (2026-11-02):

- **As known at.** A row counts for an as-of date only if its business date and its arrival date are both on or
  before that date. The arrival gate is `known_by(as_of) = greatest(as_of, base load date)`: every base-pack row
  arrived on 2026-10-27, so dates before the load read the base pack by business date alone (otherwise the
  2025-06-30 question would have no data). After the load, a back-dated delivery never changes a past answer.
- **Positions per book.** `positions_as_of(as_of)` reads each book at its own latest file date on or before the
  as-of date. A book that was not delivered reads as unchanged; closing a book needs a delivery that says so.
- **Order and re-resolution.** Delta files run issuers, curves, instruments, ownership, ratings, positions, then
  documents, whatever their names. After each batch every null resolved id is retried through the alias view and
  filled in place (the derived column only; the raw name is never touched), and the notes rules run for ownership
  rows that became fully resolved.
- **Unresolved issuer.** An instrument whose issuer (or sole guarantor) did not resolve, or resolved only after the
  as-of date, carries UNRESOLVED_NAME; with no other channel it is an unresolved holding, never "not exposed"; with
  another channel (currency, curve) the verdict stands and the flag is attached.
- **Notes rules are curated** (`curation/ownership_notes_rules.yaml`): whole-word, case-insensitive phrases mapped to
  a predicate, and a negation list; a negated note produces no row and is reported as DISCARD.
- **Unknown label or book** = granted to no user in the entitlements file: stored, flagged UNKNOWN_LABEL /
  UNKNOWN_BOOK, visible to the admin role only.
- **Re-sent documents** are matched by content hash (a desk line also by time and author) and skipped.
- **Malformed input** is reported as `path:line: reason`; a UTF-8 BOM and CRLF are accepted; the batch stays atomic.
- **Same-source updates** are SUPERSEDED, not CONFLICT; audit-only changes are skipped; a change in a dropped column
  is logged once per file per run as ignored.

Rules added after the code review (2026-11-02):

- **Paths respect a person's ruling.** While no one has confirmed a row on a link, every row on it is walkable, so
  research can show an unconfirmed channel at low grade (Meridian via the desk view). Once the link's winner is
  CONFIRMED, only rows that agree with it are walkable and the overruled rows never make a hop; a confirmed denial
  (holds = false) blocks the link. Confirm GB on Meridian and INS-1009 reads "no"; confirm Corvana and it reads "yes"
  on a high-grade channel.
- **The contradiction guard** compares a new reference-grade row with the link's current winner only.
- **A vehicle's country of risk** is derived once per batch over all issuers and ownership, so a vehicle and its
  "financing vehicle" note in one delivery take the parent's country; a note arriving later supersedes the rule's
  older row.
- **RATING_LAG is per agency**: the subject's latest rating per agency against the guarantor's latest from the same
  agency; subject `issuer|GUARANTEED_BY|guarantor|agency`.
- **The summary cap** keeps exposed holdings first (yes, unconfirmed, no), then by size; unresolved holdings are
  never omitted.
- **The hidden count** takes the asking role from the session, never from a parameter, with the search path pinned.
  It is only as strong as the connection: the tools still connect as a superuser and `SET ROLE` down, so raw SQL
  inside a tools session could switch role. A non-superuser application role closes that (TODO, first item).

## 13. Tools: what each call returns, and how much

Every tool takes `user` first and an optional `as_of`. Results are pydantic models; every cited fact carries an edge
or statement id, source system and file, as-of, quote, status. The agent reads summaries first and drills down.

| tool | returns | size rule |
|---|---|---|
| find_entity(user, query) | matches by any name, exact first | small |
| get_positions(user, as_of) | the user's positions, resolved or flagged | one row per position |
| get_exposure(user, target, as_of, detail='summary', max_documents=10, max_positions=200) | per position: verdict (yes / unconfirmed / no), channels (key, label, grade, hop count, one edge id per hop: the precedence winner), flag kind + message; **unresolved holdings in their own block** (`unresolved`: position, flag message), so there is no "unknown" verdict in the positions list; selected research: id, title, date, label, summary, topics, path entities it is about | summary by default; `detail='full'` gives the hop-by-hop shape with text. Documents ranked in SQL (`research_for_paths`) by number of path entities matched, then recency, then id; capped in both modes. The agent gets summary only; MCP exposes both |
| get_path(user, instrument_id, target, channel_key, as_of) | the representative path: hops with every citation, plus `paths_considered` | the drill-down for one channel |
| get_statements(user, entity_id, predicate, as_of) | current per link, other sources, flags, per-link hidden count | one entity |
| get_documents(user, entity_id, since, as_of, text=False) | documents about the entity: id, title, date, label, summary, topics; text only on request | summaries by default |
| get_document(user, document_id) | one document with its text | the citation fetch |
| get_ratings(user, issuer_id, as_of) | event log, current, notches vs sovereign | small |

Unresolved positions: never resolved by guess; the UNRESOLVED_REF message names the nearest known identifier of the
same kind within edit distance 1 when one exists ("nearest known ISIN XS2812345671; not applied").


# TODO

Open work after the proof of concept, roughly in the order we expect to pick it up. The reasoning behind the design
is in `narrative.md` and `ai_tooling_notes.md`. The second half lists the known issues found in testing, including an ingest
stress test run on a copy of the database with thirteen synthetic deliveries (2026-11-02).

## Next two weeks

- [ ] **Confirm/reject command with audit.** The precedence rule already ranks CONFIRMED above file values and rules
  and marks the overridden rows SUPERSEDED; nothing moves a row except SQL by hand. Add `kl-review list | confirm |
  reject <id> --by <name>` and record who decided and when.
- [ ] **Extractor as a reviewed step.** Relationship extraction is prototyped (`kl-annotate --extract`,
  `scripts/extract_trials.py`); recall varies between runs (3/2/2 of 3 on the delta note). Prompt for completeness,
  store proposals as PROPOSED for review, measure recall on a labelled set before switching it on for deltas.
- [ ] **Recency for documents.** Research is ranked by breadth then date and capped; nothing retires an old note.
  Add a recency window parameter, top-k per path entity, and a same-publisher supersession rule.
- [ ] **Trust by publisher and author**, not only by source system (a desk line and a filed broker note are both tier 1).
- [ ] **History for level-1 rows.** A changed existing key is discarded and logged; nothing is versioned. Temporal
  tables or a change log before deltas start changing existing keys.
- [ ] **Non-superuser application role, first.** The tools connect as a superuser and `SET ROLE` down, so raw SQL
  inside a tools session could switch role or reset it and see everything; the hidden-count function is only as
  strong as this. Create an application role that is a member of the user roles and nothing more, and connect as it.
- [ ] **Identity from the session.** `user` is an argument on the MCP tools because the proof of concept has no
  login; in production it comes from single sign-on and the argument disappears.

## Later

- [ ] **Structured research as the source of truth.** Notes and research become human-reviewed statements that
  supersede or replace main-table fields by recency, so documents stop stacking up in the agent's context.
- [ ] **ETL/ELT for precedence and quality**, with tests, lineage and scheduling; the database keeps security and the
  point-in-time function.
- [ ] **Graph store** for the statements table when paths cross hundreds of thousands of entities (edge list with
  provenance → edges with properties; `predicate_def` → edge types; trust rule and entitlements rebuilt in the
  application layer).
- [ ] **Tool set by question log.** Saved queries for the questions that are always the same; smaller composable tools
  for the long tail.
- [ ] **Agreement and contradiction across predicates** ("golden share" vs "decoupling") as LLM proposals with human
  confirmation.
- [ ] **Named unknowns.** CorTel's holding company and CPL's strategic investor are unresolved subjects; give them
  issuer rows if they ever matter.
- [ ] **Hidden-newer count per label.** It leaks a count by design (accepted compromise); decide per visibility label
  at firm scale. Query audit logging (pgaudit); controls on exports.

## Known issues found in testing

Ticked items were fixed on 2026-11-02 and are pinned by `tests/test_regressions.py` and the stress suite; a code review
the same day found and fixed eight more (paths ignoring a person's ruling, the hidden count's caller-supplied user,
rating lag across agencies, a vehicle's country when it arrives with its ownership row, the summary cap ranking,
the contradiction guard, the validator's position dates, filters for the ingest and the walk); a code review
the same day found and fixed eight more (paths ignoring a person's ruling, the hidden count's caller-supplied user,
rating lag across agencies, a vehicle's country when it arrives with its ownership row, the summary cap ranking,
the contradiction guard, the validator's position dates, filters for the ingest and the walk)
(`uv run pytest -m stress`, rebuilds a scratch database). `[~]` = partly addressed.

Ranked by effect on the answer. All reproduced on a copy of the database (`corvana_kl_stress`) with synthetic
delivery folders; the submitted database is untouched.

- [x] **Look-ahead in point-in-time answers.** File-held links are dated by business date (`ownership.as_of_date`,
  `ratings.action_date`), not by when the row arrived. A back-dated row delivered later changes a past answer (an
  ownership row delivered 2026-10-29 dated 2026-10-15 makes the 2026-10-27 CPL stake read 34%). Needs a known-at date
  (`updated_on <= as_of`) beside the business date in `current_statements`.
- [x] **Partial position delivery hides whole books.** Positions are read at `max(as_of_date)` over all visible rows;
  a file containing one book only makes the other book vanish for that date. Use the latest date per book.
- [x] **Delta files applied in alphabetical order.** `instruments_delta` runs before `issuers_delta`, so an instrument
  whose issuer arrives in the same batch stays UNRESOLVED_NAME, and a rerun skips it as identical. Fixed table order
  and re-resolution of null ids on each ingest.
- [x] **An unresolved issuer reads as "not exposed".** A bond whose issuer did not resolve comes back `exposed: no`
  with no flag at the position. It must read "unknown", like an unresolved ref. False negative on the core question.
- [x] **`ownership.notes` rule matches substrings.** "Sovereign guarantee withdrawn ..." produced a GUARANTEED_BY
  holds=true row. The rule needs a negation check or a curated phrase list.
- [x] **Unknown visibility label or book hides silently.** A note labelled with a label that has no role, or a
  position in a book with no role, is stored and seen by nobody without a flag (the validator catches the label,
  nothing catches the book). Flag both at ingest.
- [x] **Delta desk notes have no label**, because `desk_notes.yaml` is keyed by exact path; they are hidden and flagged
  UNLABELLED_DOCUMENT, which is right, but the label should follow the file's origin.
- [x] **Desk-note parser** drops handles containing a dot (`j.s:`), appending the line to the previous entry.
- [x] **A re-delivered note is stored twice** (the unique key includes the delivery path); dedupe on content hash.
- [x] **A newer row from the same source reads as CONFLICT** (tracker 34% vs tracker 51%, both REFERENCE). The value
  is right, the kind is wrong: a same-source update should be SUPERSEDED.
- [~] **Discard noise versus silent loss.** (audit-only changes now skipped; dropped-column changes logged once per file per run; a respelled name is still a discard) A `last_updated` bump or a respelled issuer name is discarded and
  re-reported on every re-delivery; a change in a dropped column (maturity, sector) is skipped as identical.
- [~] **Malformed files roll back atomically (good) but opaquely** (errors now name file and line; one bad file still blocks its batch): messages lack file and line, and one bad file blocks
  the good files in its batch.
- [x] **Alias scan misses encoded and dotted names** ("Corvana &amp; Light", "C.N.O.C.").
- [~] **Scale.** (summary now capped by `max_positions`; ingest throughput and latency at volume not addressed) 13.8k rows ingest in 57 s row by row; at 4,000 positions per book `get_exposure` takes 6 s and the
  summary is 2.2M chars: summary size grows with positions and needs a cap or paging. Duplicate instrument
  descriptions (RegS/144A pairs) break alias uniqueness and are only caught by the validator after the ingest.
- [ ] **Smaller items**: the summary payload is about 3.2k tokens (flag messages repeat per source); nested
  cross-type spans in the scan are kept by the rule and marked null by the model (harmless); a country chosen as
  "about" has no column; confidences are reported, not stored; `predicate_def` rows live in a curation CSV and must
  stay in step with the DBML note.

Held up under the same test: reruns are no-ops; a same-key rating with a new value is discarded; a new issuer's
names enter the scan for documents of the same batch; RATING_LAG on CDB closes when its rating arrives; row-level
security fails closed.


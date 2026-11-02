# Expected: "What was the state's stake in Corvana Power & Light on 2025-06-30, and what is it now?"

Tool: get_statements(user, entity_id=ISS-0003, predicate=OWNS, as_of=...). Rows about ISS-0001 -> ISS-0003.

## Rows in the database

| id | value | as_of | source | status | visibility |
|---|---|---|---|---|---|
| tracker | 51 | 2023-12-31 | ownership.csv (OwnershipTracker, tier 2) | REFERENCE | everyone |
| bank-a-2024 | 51 | 2024-05-14 | Bank A 2024-05-14 | PROPOSED | external |
| ipo-note | 34 | 2026-02-24 | Internal EM Credit 2026-03-05 | PROPOSED | credit_internal |
| ipo-note (strategic investor, owner unresolved) | 25 | 2026-02-24 | same | PROPOSED | credit_internal |

## as_of = 2025-06-30

- alice, bob, carol: current = 51 (tracker, REFERENCE); other_sources = Bank A 51 (CORROBORATED). No flags.
  hidden_newer_count = 0 for everyone (the IPO rows are after the date).

## as_of = 2026-10-27 (now)

- alice: current = 51 (tracker, as_of 2023-12-31). Flags: none visible. hidden_newer_count = 1 (a newer statement
  she cannot read). Narrative must say the reference value is 34 months old and that newer information exists
  that she is not entitled to see, without revealing it.
- bob, carol: current = 51 (tracker, REFERENCE, wins by trust rule). Flags: STALE (newer lower-tier row disagrees).
  other_sources: 34 (credit_internal, 2026-02-24, quote "The government sold down its stake from 51% to 34%").
  Narrative: "The tracker says 51% but it dates from 2023; internal research says the stake fell to 34% at the
  February 2026 IPO. The tracker is likely stale." Both numbers and both citations must appear.

# Expected: entitlement negatives (enforced in Postgres RLS, observable through the tools)

- get_positions(alice) returns exactly the 6 EM_MACRO rows; get_positions(bob) exactly the 8 EM_CREDIT rows;
  get_positions(carol) all 14.
- get_documents(alice) never includes source_file research/2026-03-05_em-credit-internal_cpl-ipo.md or any desk_notes row.
- get_documents(bob) never includes research/2026-08-21_macro-internal_cvd-reserves.md.
- get_statements(alice, ISS-0003, OWNS) never returns the 34 or 25 rows; hidden_newer_count = 1 at as_of now.
- get_documents(bob, INS-1004) returns no macro_internal document; get_documents(alice, ISS-0003) returns no credit_internal document.
- get_exposure(alice, ISS-0001) lists no EM_CREDIT instrument; get_exposure(bob, ISS-0001) lists no EM_MACRO instrument.
- Reference tables (issuers, instruments, curves, ratings, country, rating_scale, sources) are identical for all users.
- psql as role alice: `select count(*) from positions` = 6; `select count(*) from documents where visibility='credit_internal'` = 0.
- Role memberships in Postgres equal entitlements.yaml (validate.py check).

# Expected: alice, "If the Republic of Corvana is downgraded, what in my book is exposed, how, and what does our research say?"

As of 2026-10-27 (base pack). alice: book EM_MACRO; research visibility external, macro_internal.
Target: ISS-0001 Republic of Corvana. Current rating BB- / Negative (Agency A, 2026-09-18).

## Positions and channels

| ref | instrument | qty | exposed | channels (path to ISS-0001) | status of the links |
|---|---|---|---|---|---|
| XS2812345671 | INS-1001 CORVAN 6.5 2030 | 15,000,000 USD | yes | ISSUED_BY ISS-0001 | REFERENCE (SecMaster, legal name) |
| QC000CV33031 | INS-1004 CVGB 10.5 2033 | 450,000,000 CVD | yes | ISSUED_BY ISS-0001; DENOMINATED_IN CVD -> QC -> sovereign; PRICED_OFF CVD-GOVT -> CVD -> QC -> sovereign | ISSUED_BY is INFERRED (alias "Corvana Ministry of Finance"); currency and curve links REFERENCE |
| INS-2002 | USD/CVD NDF 3M | 25,000,000 USD | yes | DENOMINATED_IN CVD -> QC -> sovereign | REFERENCE |
| CVD IRS 5Y | INS-2003 CVD IRS 5Y | 800,000,000 CVD | yes | DENOMINATED_IN CVD; PRICED_OFF CVD-OIS -> CVD -> QC -> sovereign | REFERENCE |
| XS2900123451 | INS-1010 VALDOR 8 2031 | 8,000,000 USD | research only | ISSUED_BY ISS-0009; ISS-0009 CORRELATED_WITH ISS-0001 (0.7) | CORRELATED_WITH is PROPOSED (Bank B 2025-11-18, external); same note denies proxy (TRADES_AS_PROXY_FOR holds=false) |
| GB00NB123454 | INS-1011 NBRTL 4.25 2029 | 5,000,000 GBP | no | none | |

Unresolved refs: none in EM_MACRO.

## Research alice can read, by entity on a path

- ISS-0001: Bank A 2024-05-14 (stable BB-, overweight CORVAN 2035s vs Valdoria 2031s); Bank B 2026-09-22 (~60%
  one-notch downgrade in 6 months, buy 5Y CDS protection); internal macro 2026-08-21 (downgrade -> CVGB outflows,
  CVD govt curve higher/steeper, 2033 most exposed, pay CVD 5Y swaps, long USD/CVD via 3M NDFs).
- INS-1004, INS-2002, INS-2003, CVD, CVD-GOVT: the macro note is about them (documents.about_instruments /
  about_curves / about_currencies, macro_internal); get_documents(alice, INS-1004) returns it, get_documents(bob,
  INS-1004) does not. INS-1004 is named only as "the 2033": no alias covers it, the grounded annotator adds it from
  context (an added mention with verbatim text and a confidence above the threshold).
- ISS-0009: Bank B 2025-11-18 (proxy overstated; CDS correlation ~0.7); Bank B 2026-09-22 (some spillover likely).
- ISS-0010 / INS-1011: Bank A 2026-07-01 Market Weight. Not on a path; may be listed as "not exposed".

## Must NOT appear

- The CPL IPO note (credit_internal) or any statement from it (34% stake, beta 0.6).
- Any desk-note line (credit_internal by assumption).
- Any EM_CREDIT position.

## Data-quality rows that may be shown

- None are required on alice's paths. The Valdoria proxy denial (holds=false) vs correlation 0.7 is the same
  source and not a conflict.

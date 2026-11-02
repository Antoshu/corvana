# Expected: bob, same question

As of 2026-10-27 (base pack). bob: book EM_CREDIT; research visibility external, credit_internal (includes desk notes).
Target: ISS-0001. Current rating BB- / Negative.

## Positions and channels

| ref | instrument | qty | exposed | channels (path to ISS-0001) | status of the links |
|---|---|---|---|---|---|
| XS2812345672 | unresolved | 10,000,000 USD | unknown | none | UNRESOLVED_REF flag (matches no ISIN; not treated as a typo of INS-1001) |
| CNOC 5.875 11/04/29 | INS-1005 CNOC Finance 5.875 2029 | 12,000,000 USD | yes | ISSUED_BY ISS-0007; INS-1005 GUARANTEED_BY ISS-0002; ISS-0007 FINANCING_VEHICLE_OF ISS-0002; ISS-0007 GUARANTEED_BY ISS-0002; ISS-0002 OWNED BY ISS-0001 100%; ISS-0002 RATING_CAPPED_BY ISS-0001; ISS-0002 TRADES_AS_PROXY_FOR ISS-0001; ISS-0007 COUNTRY_OF_RISK QC | ISSUED_BY REFERENCE (legal name); instrument guarantee INFERRED (alias "Corvana National Oil Co"); vehicle INFERRED (ownership.notes); OWNS REFERENCE (tracker 2020-06-30), corroborated by Bank A 2024 and 2026; issuer guarantee, rating cap, proxy PROPOSED (external research); COUNTRY_OF_RISK INFERRED (vehicle rule) |
| XS2500445569 | INS-1006 CPL 6 2031 | 7,500,000 USD | yes | ISSUED_BY ISS-0003; ISS-0003 OWNED BY ISS-0001; ISS-0003 BETA_TO ISS-0001 0.6 | ISSUED_BY INFERRED (alias); OWNS current = 51% REFERENCE (tracker 2023-12-31) with STALE flag; other_sources = 34% PROPOSED (credit_internal 2026-02-24) and 25% strategic investor; BETA_TO PROPOSED credit_internal |
| INS-1007 | INS-1007 CDB 4.75 2027 | 6,000,000 USD | yes | ISSUED_BY ISS-0004; INS-1007 GUARANTEED_BY ISS-0001; ISS-0004 GUARANTEED_BY ISS-0001; ISS-0004 OWNED BY ISS-0001 100% | ISSUED_BY REFERENCE; instrument guarantee REFERENCE (guarantor_name = legal name); issuer guarantee INFERRED (ownership.notes), CORROBORATED by Bank A 2024, Bank B 2026-09-22, desk 2026-09-19; OWNS REFERENCE (2022-12-31) |
| XS2700334415 | INS-1008 CorTel 5.5 2032 | 9,000,000 USD | yes | ISSUED_BY ISS-0005; ISS-0005 COUNTRY_OF_RISK QC -> sovereign; ISS-0005 OWNED BY ISS-0001; ISS-0005 TRADES_AS_PROXY_FOR ISS-0001 | ISSUED_BY INFERRED (alias); COUNTRY_OF_RISK INFERRED (incorporation QC) is the only high-grade channel, so CorTel is exposed as a Corvana-domiciled issuer; the ownership and proxy channels are research/desk only. OWNS has no reference row: current = 20% PROPOSED (desk 2026-02-11, credit_internal), earlier 35% indirect (Bank A 2023-10-02); proxy: holds=true (desk 2026-02-11) supersedes holds=false "standalone credit" (Bank A 2023-10-02) |
| XS2300665523 | INS-1009 Meridian 7 2030 | 4,000,000 USD | desk view only | ISSUED_BY ISS-0008; ISS-0008 COUNTRY_OF_RISK QC -> sovereign | ISSUED_BY REFERENCE; COUNTRY_OF_RISK current = GB INFERRED (incorporation), CONFLICT flag with PROPOSED QC (desk js 2026-04-30, credit_internal). Shown as exposure under an unconfirmed desk view |
| INS-2001 | INS-2001 CORVAN 5Y CDS | -20,000,000 USD | yes | REFERENCES_CREDIT ISS-0001 | REFERENCE. Sign convention undocumented; report as-is |
| XS2999887768 | unresolved (resolves to INS-1012 after the 2026-10-28 delta) | 5,000,000 USD | unknown | none | UNRESOLVED_REF flag |

## Research bob can read, by entity on a path

- ISS-0001: Bank A 2024-05-14; Bank B 2026-09-22. NOT the macro note (macro_internal).
- ISS-0002 / ISS-0007: Bank A 2024-05-14 (trades tightly with sovereign), Bank A 2026-06-10 (100% MinFin, unconditional
  parent guarantee, 20-30bp wide), Bank B 2026-09-22 (rating capped, one-for-one).
- ISS-0003: CPL IPO note 2026-03-05 (34%, beta 0.6, golden share); Bank A 2024 (51%, modest pick-up); desk 2026-09-19 ("CPL less so now post IPO").
- ISS-0004: Bank A 2024, Bank B 2026-09-22, desk 2026-09-19 ("treat like sovereign").
- ISS-0005: Bank A 2023-10-02 (standalone, one notch above sovereign), desk 2026-02-11 (proxy, 20%).
- ISS-0008: desk 2026-04-30.
- INS-2001: Bank B 2026-09-22 recommends buying 5Y protection.
- ISS-0006 FCB: not in book; may be mentioned only if the agent asks about the sovereign-bank nexus.

## Must NOT appear

- The macro note (macro_internal) or its views.
- Any EM_MACRO position.

## Data-quality rows expected on bob's paths

- UNRESOLVED_REF: XS2812345672, XS2999887768.
- STALE: OWNS ISS-0001 -> ISS-0003 (tracker 51% vs newer 34%).
- CONFLICT / CONTRADICTS_REFERENCE: COUNTRY_OF_RISK ISS-0008 (GB vs QC).
- CORROBORATED: GUARANTEED_BY ISS-0004 -> ISS-0001 (4 sources); OWNS ISS-0001 -> ISS-0002 (3 sources).
- Superseded (history, not conflict): TRADES_AS_PROXY_FOR ISS-0005 holds=false (2023) then true (2026).

## Note on the trust rule

Every issuer incorporated in Corvana carries an INFERRED COUNTRY_OF_RISK = QC row, so CNOC, CPL, CDB and CorTel all
have a reference-grade "country of risk" channel in addition to their specific ones. Only issuers outside Corvana
(Meridian via a desk note, Valdoria via a research correlation) can be "unconfirmed".

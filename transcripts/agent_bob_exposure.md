# Agent transcript: bob, as of 2026-10-27

Model: claude-opus-5-5

## Question

If the Republic of Corvana is downgraded, what in my book is exposed, how, and what does our research say about it?

## Tool calls

### 1. find_entity(query='Republic of Corvana')

<details><summary>result</summary>

```json
[
  {
    "entity_type": "issuer",
    "entity_id": "ISS-0001",
    "name": "Republic of Corvana",
    "matched_alias": "Republic of Corvana",
    "match_kind": "exact"
  }
]
```

</details>

### 2. get_exposure(target_id='ISS-0001', max_documents=10)

<details><summary>result</summary>

```json
{
  "user": "bob",
  "as_of": "2026-10-27",
  "target": {
    "entity_type": "issuer",
    "entity_id": "ISS-0001",
    "name": "Republic of Corvana",
    "matched_alias": "ISS-0001",
    "match_kind": "exact"
  },
  "target_rating": {
    "issuer_id": "ISS-0001",
    "current": {
      "agency": "Agency A",
      "rating": "BB-",
      "outlook": "Negative",
      "action_date": "2026-09-18",
      "rank": 13
    },
    "history": [
      {
        "agency": "Agency A",
        "rating": "BB-",
        "outlook": "Negative",
        "action_date": "2026-09-18",
        "rank": 13
      },
      {
        "agency": "Agency A",
        "rating": "BB-",
        "outlook": "Stable",
        "action_date": "2024-04-10",
        "rank": 13
      }
    ],
    "sovereign_issuer_id": "ISS-0001",
    "sovereign_current": {
      "agency": "Agency A",
      "rating": "BB-",
      "outlook": "Negative",
      "action_date": "2026-09-18",
      "rank": 13
    },
    "notches_vs_sovereign": 0
  },
  "positions": [
    {
      "position": {
        "book": "EM_CREDIT",
        "instrument_ref": "CNOC 5.875 11/04/29",
        "ref_type": "TICKER",
        "quantity": "12000000.00",
        "notional_ccy": "USD",
        "as_of_date": "2026-10-27",
        "instrument_id": "INS-1005",
        "description": "CNOC Finance 5.875% 2029",
        "instrument_type": "Corporate Bond",
        "resolution_note": "resolved by TICKER"
      },
      "exposed": "yes",
      "channels": [
        {
          "key": "OWNS",
          "label": "state-owned (100% stake) via Corvana National Oil Company",
          "grade": "high",
          "hop_count": 2,
          "edge_ids": [
            "instruments:INS-1005:guarantor_id",
            "ownership:1"
          ],
          "paths_considered": 4
        },
        {
          "key": "RATING_CAPPED_BY",
          "label": "rating capped at the sovereign via Corvana National Oil Company",
          "grade": "low",
          "hop_count": 2,
          "edge_ids": [
            "instruments:INS-1005:guarantor_id",
            "stmt:27"
          ],
          "paths_considered": 4
        },
        {
          "key": "TRADES_AS_PROXY_FOR",
          "label": "trades as a sovereign proxy via Corvana National Oil Company",
          "grade": "low",
          "hop_count": 2,
          "edge_ids": [
            "instruments:INS-1005:guarantor_id",
            "stmt:16"
          ],
          "paths_considered": 4
        },
        {
          "key": "COUNTRY_OF_RISK>SOVEREIGN_IS",
          "label": "country of risk is the sovereign's via Corvana National Oil Company",
          "grade": "high",
          "hop_count": 3,
          "edge_ids": [
            "instruments:INS-1005:guarantor_id",
            "stmt:4",
            "country:QC:sovereign_issuer_id"
          ],
          "paths_considered": 5
        }
      ],
      "flags": [
        {
          "kind": "CORROBORATED",
          "message": "ISS-0001 OWNS ISS-0002: current 100 (REFERENCE, OwnershipTracker, as_of 2020-06-30) vs 100 (PROPOSED, ResearchHub, as_of 2026-06-10)"
        },
        {
          "kind": "CORROBORATED",
          "message": "ISS-0001 OWNS ISS-0002: current 100 (REFERENCE, OwnershipTracker, as_of 2020-06-30) vs 100 (PROPOSED, ResearchHub, as_of 2024-05-14)"
        },
        {
          "kind": "CORROBORATED",
          "message": "ISS-0007 FINANCING_VEHICLE_OF ISS-0002: current ISS-0002 (INFERRED, OwnershipTracker, as_of 2021-03-01) vs ISS-0002 (PROPOSED, ResearchHub, as_of 2026-06-10)"
        },
        {
          "kind": "CORROBORATED",
          "message": "ISS-0007 GUARANTEED_BY ISS-0002: current true (PROPOSED, ResearchHub, as_of 2026-09-22) vs true (PROPOSED, ResearchHub, as_of 2026-06-10)"
        }
      ]
    },
    {
      "position": {
        "book": "EM_CREDIT",
        "instrument_ref": "INS-1007",
        "ref_type": "INTERNAL",
        "quantity": "6000000.00",
        "notional_ccy": "USD",
        "as_of_date": "2026-10-27",
        "instrument_id": "INS-1007",
        "description": "Corvana Development Bank 4.75% 2027",
        "instrument_type": "Agency Bond",
        "resolution_note": "resolved by INTERNAL"
      },
      "exposed": "yes",
      "channels": [
        {
          "key": "GUARANTEED_BY",
          "label": "guaranteed by Republic of Corvana",
          "grade": "high",
          "hop_count": 1,
          "edge_ids": [
            "instruments:INS-1007:guarantor_id"
          ],
          "paths_considered": 2
        },
        {
          "key": "OWNS",
          "label": "state-owned (100% stake)",
          "grade": "high",
          "hop_count": 2,
          "edge_ids": [
            "instruments:INS-1007:issuer_id",
            "ownership:2"
          ],
          "paths_considered": 1
        },
        {
          "key": "COUNTRY_OF_RISK>SOVEREIGN_IS",
          "label": "country of risk is the sovereign's",
          "grade": "high",
          "hop_count": 3,
          "edge_ids": [
            "instruments:INS-1007:issuer_id",
            "stmt:6",
            "country:QC:sovereign_issuer_id"
          ],
          "paths_considered": 1
        }
      ],
      "flags": [
        {
          "kind": "CORROBORATED",
          "message": "ISS-0004 GUARANTEED_BY ISS-0001: current true (INFERRED, OwnershipTracker, as_of 2022-12-31) vs true (PROPOSED, ResearchHub, as_of 2026-09-22)"
        },
        {
          "kind": "CORROBORATED",
          "message": "ISS-0004 GUARANTEED_BY ISS-0001: current true (INFERRED, OwnershipTracker, as_of 2022-12-31) vs true (PROPOSED, DeskNotes, as_of 2026-09-19)"
        },
        {
          "kind": "CORROBORATED",
          "message": "ISS-0004 GUARANTEED_BY ISS-0001: current true (INFERRED, OwnershipTracker, as_of 2022-12-31) vs true (PROPOSED, ResearchHub, as_of 2024-05-14)"
        }
      ]
    },
    {
      "position": {
        "book": "EM_CREDIT",
        "instrument_ref": "INS-2001",
        "ref_type": "INTERNAL",
        "quantity": "-20000000.00",
        "notional_ccy": "USD",
        "as_of_date": "2026-10-27",
        "instrument_id": "INS-2001",
        "description": "Corvana 5Y senior CDS",
        "instrument_type": "CDS",
        "resolution_note": "resolved by INTERNAL"
      },
      "exposed": "yes",
      "channels": [
        {
          "key": "REFERENCES_CREDIT",
          "label": "CDS protection referencing the sovereign",
          "grade": "high",
          "hop_count": 1,
          "edge_ids": [
            "instruments:INS-2001:issuer_id"
          ],
          "paths_considered": 1
        }
      ],
      "flags": []
    },
    {
      "position": {
        "book": "EM_CREDIT",
        "instrument_ref": "XS2300665523",
        "ref_type": "ISIN",
        "quantity": "4000000.00",
        "notional_ccy": "USD",
        "as_of_date": "2026-10-27",
        "instrument_id": "INS-1009",
        "description": "Meridian Mining 7% 2030",
        "instrument_type": "Corporate Bond",
        "resolution_note": "resolved by ISIN"
      },
      "exposed": "unconfirmed",
      "channels": [
        {
          "key": "COUNTRY_OF_RISK>SOVEREIGN_IS",
          "label": "country of risk is the sovereign's",
          "grade": "low",
          "hop_count": 3,
          "edge_ids": [
            "instruments:INS-1009:issuer_id",
            "stmt:32",
            "country:QC:sovereign_issuer_id"
          ],
          "paths_considered": 1
        }
      ],
      "flags": [
        {
          "kind": "CONFLICT",
          "message": "ISS-0008 COUNTRY_OF_RISK GB: current GB (INFERRED, SecMaster, as_of 2026-04-30) vs QC (PROPOSED, DeskNotes, as_of 2026-04-30)"
        }
      ]
    },
    {
      "position": {
        "book": "EM_CREDIT",
        "instrument_ref": "XS2500445569",
        "ref_type": "ISIN",
        "quantity": "7500000.00",
        "notional_ccy": "USD",
        "as_of_date": "2026-10-27",
        "instrument_id": "INS-1006",
        "description": "Corvana Power & Light 6% 2031",
        "instrument_type": "Corporate Bond",
        "resolution_note": "resolved by ISIN"
      },
      "exposed": "yes",
      "channels": [
        {
          "key": "OWNS",
          "label": "state-owned (51% stake)",
          "grade": "high",
          "hop_count": 2,
          "edge_ids": [
            "instruments:INS-1006:issuer_id",
            "ownership:3"
          ],
          "paths_considered": 1
        },
        {
          "key": "BETA_TO",
          "label": "spread beta 0.6 to the sovereign",
          "grade": "low",
          "hop_count": 2,
          "edge_ids": [
            "instruments:INS-1006:issuer_id",
            "stmt:23"
          ],
          "paths_considered": 1
        },
        {
          "key": "COUNTRY_OF_RISK>SOVEREIGN_IS",
          "label": "country of risk is the sovereign's",
          "grade": "high",
          "hop_count": 3,
          "edge_ids": [
            "instruments:INS-1006:issuer_id",
            "stmt:5",
            "country:QC:sovereign_issuer_id"
          ],
          "paths_considered": 1
        }
      ],
      "flags": [
        {
          "kind": "STALE",
          "message": "ISS-0001 OWNS ISS-0003: current 51 (REFERENCE, OwnershipTracker, as_of 2023-12-31) vs 34 (PROPOSED, ResearchHub, as_of 2026-02-24)"
        },
        {
          "kind": "CORROBORATED",
          "message": "ISS-0001 OWNS ISS-0003: current 51 (REFERENCE, OwnershipTracker, as_of 2023-12-31) vs 51 (PROPOSED, ResearchHub, as_of 2024-05-14)"
        }
      ]
    },
    {
      "position": {
        "book": "EM_CREDIT",
        "instrument_ref": "XS2700334415",
        "ref_type": "ISIN",
        "quantity": "9000000.00",
        "notional_ccy": "USD",
        "as_of_date": "2026-10-27",
        "instrument_id": "INS-1008",
        "description": "CorTel 5.5% 2032",
        "instrument_type": "Corporate Bond",
        "resolution_note": "resolved by ISIN"
      },
      "exposed": "yes",
      "channels": [
        {
          "key": "OWNS",
          "label": "state-owned (20% stake)",
          "grade": "low",
          "hop_count": 2,
          "edge_ids": [
            "instruments:INS-1008:issuer_id",
            "stmt:31"
          ],
          "paths_considered": 1
        },
        {
          "key": "TRADES_AS_PROXY_FOR",
          "label": "trades as a sovereign proxy",
          "grade": "low",
          "hop_count": 2,
          "edge_ids": [
            "instruments:INS-1008:issuer_id",
            "stmt:30"
          ],
          "paths_considered": 1
        },
        {
          "key": "COUNTRY_OF_RISK>SOVEREIGN_IS",
          "label": "country of risk is the sovereign's",
          "grade": "high",
          "hop_count": 3,
          "edge_ids": [
            "instruments:INS-1008:issuer_id",
            "stmt:7",
            "country:QC:sovereign_issuer_id"
          ],
          "paths_considered": 1
        }
      ],
      "flags": [
        {
          "kind": "SUPERSEDED",
          "message": "ISS-0001 OWNS ISS-0005: current 20 (PROPOSED, DeskNotes, as_of 2026-02-11) vs 35 (PROPOSED, ResearchHub, as_of 2023-10-02)"
        },
        {
          "kind": "SUPERSEDED",
          "message": "ISS-0005 TRADES_AS_PROXY_FOR ISS-0001: current true (PROPOSED, DeskNotes, as_of 2026-02-11) vs false (PROPOSED, ResearchHub, as_of 2023-10-02)"
        }
      ]
    }
  ],
  "unresolved": [
    {
      "position": {
        "book": "EM_CREDIT",
        "instrument_ref": "XS2812345672",
        "ref_type": "ISIN",
        "quantity": "10000000.00",
        "notional_ccy": "USD",
        "as_of_date": "2026-10-27",
        "instrument_id": null,
        "description": null,
        "instrument_type": null,
        "resolution_note": "matches no instrument; not guessed"
      },
      "flag_message": "position EM_CREDIT/XS2812345672 (ISIN) matches no instrument known on 2026-10-27; nearest known ISIN XS2812345671 (INS-1001); not applied"
    },
    {
      "position": {
        "book": "EM_CREDIT",
        "instrument_ref": "XS2999887768",
        "ref_type": "ISIN",
        "quantity": "5000000.00",
        "notional_ccy": "USD",
        "as_of_date": "2026-10-27",
        "instrument_id": null,
        "description": null,
        "instrument_type": null,
        "resolution_note": "matches no instrument; not guessed"
      },
      "flag_message": "position EM_CREDIT/XS2999887768 (ISIN) matches no instrument known on 2026-10-27"
    }
  ],
  "research": [
    {
      "document_id": 8,
      "title": "Republic of Corvana - Outlook to Negative; downgrade risk rising",
      "publisher": "Bank B Research",
      "published_at": "2026-09-22T00:00:00",
      "visibility": "external",
      "summary": "Bank B Research says Agency A's negative outlook on the Republic of Corvana raises downgrade risk, discusses read-across to CNOC, CDB, First Corvana Bank and Valdoria, and recommends buying 5Y CDS protection on the sovereign.",
      "topics": [
        "outlook negative",
        "downgrade risk",
        "sovereign-bank nexus",
        "guarantee",
        "cds"
      ],
      "about_on_path": [
        "INS-2001",
        "ISS-0001",
        "ISS-0002",
        "ISS-0004"
      ]
    },
    {
      "document_id": 2,
      "title": "Corvana - Steady as she goes",
      "publisher": "Bank A Research",
      "published_at": "2024-05-14T00:00:00",
      "visibility": "external",
      "summary": "A research note reiterating a stable BB- view on the Republic of Corvana, reviewing its state-linked issuers, and recommending an overweight in the Corvana 2035s against Valdoria 2031s.",
      "topics": [
        "sovereign credit",
        "quasi-sovereigns",
        "state ownership",
        "guarantee",
        "relative value"
      ],
      "about_on_path": [
        "ISS-0001",
        "ISS-0002",
        "ISS-0003",
        "ISS-0004"
      ]
    },
    {
      "document_id": 11,
      "title": null,
      "publisher": "EM Credit desk",
      "published_at": "2026-09-19T08:40:00",
      "visibility": "credit_internal",
      "summary": "A desk chat note reminding that the Corvana Development Bank 2027 bonds are guaranteed and so trade like sovereign debt, while Corvana Power & Light is less so after its IPO.",
      "topics": [
        "guarantee",
        "outlook change",
        "sovereign linkage",
        "ipo"
      ],
      "about_on_path": [
        "INS-1007",
        "ISS-0003",
        "ISS-0004"
      ]
    },
    {
      "document_id": 5,
      "title": "CNOC - Production steady, guarantee structure unchanged",
      "publisher": "Bank A Research",
      "published_at": "2026-06-10T00:00:00",
      "visibility": "external",
      "summary": "Research note on Corvana National Oil Company (CNOC) saying Q1 output was steady, the state ownership and CNOC Finance B.V. guarantee structure for USD debt are unchanged, and its bonds trade 20-30bp wide of the sovereign curve.",
      "topics": [
        "guarantee",
        "production",
        "ownership",
        "spreads",
        "sovereign curve"
      ],
      "about_on_path": [
        "ISS-0001",
        "ISS-0002"
      ]
    },
    {
      "document_id": 9,
      "title": null,
      "publisher": "EM Credit desk",
      "published_at": "2026-02-11T09:14:00",
      "visibility": "credit_internal",
      "summary": "A desk note reminding that CorTel trades as a sovereign proxy, moving with Corvana sovereign spreads despite the government's reduced 20% stake after the 2025 placement.",
      "topics": [
        "sovereign proxy",
        "ownership",
        "spreads",
        "government stake"
      ],
      "about_on_path": [
        "ISS-0001",
        "ISS-0005"
      ]
    },
    {
      "document_id": 10,
      "title": null,
      "publisher": "EM Credit desk",
      "published_at": "2026-04-30T16:02:00",
      "visibility": "credit_internal",
      "summary": "A desk note saying Meridian Mining's country of risk should be Corvana because all its mines are there, even though it is UK listed and incorporated and the risk system still shows GB.",
      "topics": [
        "country of risk",
        "meridian mining",
        "data correction",
        "domicile"
      ],
      "about_on_path": [
        "ISS-0008"
      ]
    },
    {
      "document_id": 4,
      "title": "CPL post-IPO - partial decoupling from the sovereign",
      "publisher": "Internal - EM Credit",
      "published_at": "2026-03-05T00:00:00",
      "visibility": "credit_internal",
      "summary": "Research note arguing that after its partial IPO, Corvana Power & Light should trade with a lower beta to the sovereign, while remaining exposed to a sovereign downgrade through tariffs and state receivables.",
      "topics": [
        "ipo",
        "sovereign linkage",
        "beta",
        "golden share",
        "downgrade"
      ],
      "about_on_path": [
        "ISS-0003"
      ]
    },
    {
      "document_id": 3,
      "title": "Valdoria - Neighbour risk overstated",
      "publisher": "Bank B Research",
      "published_at": "2025-11-18T00:00:00",
      "visibility": "external",
      "summary": "A research note arguing that Valdoria's role as a trading proxy for Corvana is overstated given limited bilateral trade, though 5Y CDS correlation rises in risk-off episodes.",
      "topics": [
        "proxy",
        "contagion",
        "correlation",
        "cds",
        "neighbour risk"
      ],
      "about_on_path": [
        "ISS-0001"
      ]
    },
    {
      "document_id": 1,
      "title": "CorTel - Initiating coverage",
      "publisher": "Bank A Research",
      "published_at": "2023-10-02T00:00:00",
      "visibility": "external",
      "summary": "Initiating coverage note on Corvana Telecommunications (CorTel), a 35% state-owned company viewed as a standalone credit rated one notch above the sovereign.",
      "topics": [
        "initiating coverage",
        "state ownership",
        "standalone credit",
        "sovereign linkage"
      ],
      "about_on_path": [
        "ISS-0005"
      ]
    }
  ],
  "notes": [
    "derivative sign convention is undocumented; quantities reported as in the OMS"
  ]
}
```

</details>

### 3. get_document(document_id=8)

<details><summary>result</summary>

```json
{
  "document_id": 8,
  "source_system": "ResearchHub",
  "source_file": "research/2026-09-22_bank-b_corvana-negative-watch.md",
  "kind": "RESEARCH",
  "title": "Republic of Corvana - Outlook to Negative; downgrade risk rising",
  "publisher": "Bank B Research",
  "author": "CEEMEA Credit Strategy",
  "published_at": "2026-09-22T00:00:00",
  "visibility": "external",
  "about_issuers": [
    "ISS-0001",
    "ISS-0002",
    "ISS-0004",
    "ISS-0006",
    "ISS-0007",
    "ISS-0009"
  ],
  "about_instruments": [
    "INS-2001"
  ],
  "about_curves": [],
  "about_currencies": [
    "USD"
  ],
  "topics": [
    "outlook negative",
    "downgrade risk",
    "sovereign-bank nexus",
    "guarantee",
    "cds"
  ],
  "summary": "Bank B Research says Agency A's negative outlook on the Republic of Corvana raises downgrade risk, discusses read-across to CNOC, CDB, First Corvana Bank and Valdoria, and recommends buying 5Y CDS protection on the sovereign.",
  "annotated_by": "LLM",
  "text": "\nFollowing Agency A's revision of the outlook to Negative on 18 September, we see a ~60% probability of a\none-notch downgrade to B+ within six months. Fiscal slippage from energy subsidies is the main driver.\n\nRead-across:\n- Corvana Oil (CNOC) - rating capped at the sovereign; USD bonds issued via its Dutch finance subsidiary carry\n  a full parent guarantee. Expect a one-for-one move.\n- CDB - explicitly guaranteed, will move with the sovereign.\n- First Corvana Bank - roughly 28% of assets in government securities; the sovereign-bank nexus means FCB is\n  exposed despite being privately owned.\n- Republic of Valdoria - limited direct trade linkage, but EM sovereign funds often hold both; some spillover\n  likely.\n\nWe recommend buying 5Y CDS protection on the sovereign.\n"
}
```

</details>

### 4. get_document(document_id=11)

<details><summary>result</summary>

```json
{
  "document_id": 11,
  "source_system": "DeskNotes",
  "source_file": "desk_notes/em-credit-desk-notes.md",
  "kind": "DESK_NOTE",
  "title": null,
  "publisher": "EM Credit desk",
  "author": "dk",
  "published_at": "2026-09-19T08:40:00",
  "visibility": "credit_internal",
  "about_issuers": [
    "ISS-0003",
    "ISS-0004"
  ],
  "about_instruments": [
    "INS-1007"
  ],
  "about_curves": [],
  "about_currencies": [],
  "topics": [
    "guarantee",
    "outlook change",
    "sovereign linkage",
    "ipo"
  ],
  "summary": "A desk chat note reminding that the Corvana Development Bank 2027 bonds are guaranteed and so trade like sovereign debt, while Corvana Power & Light is less so after its IPO.",
  "annotated_by": "LLM",
  "text": "after the outlook change - remember CDB 27s are guaranteed so treat like sovereign.\nCPL less so now post IPO."
}
```

</details>

### 5. get_document(document_id=4)

<details><summary>result</summary>

```json
{
  "document_id": 4,
  "source_system": "ResearchHub",
  "source_file": "research/2026-03-05_em-credit-internal_cpl-ipo.md",
  "kind": "RESEARCH",
  "title": "CPL post-IPO - partial decoupling from the sovereign",
  "publisher": "Internal - EM Credit",
  "author": "EM Credit desk analyst",
  "published_at": "2026-03-05T00:00:00",
  "visibility": "credit_internal",
  "about_issuers": [
    "ISS-0003"
  ],
  "about_instruments": [],
  "about_curves": [],
  "about_currencies": [],
  "topics": [
    "ipo",
    "sovereign linkage",
    "beta",
    "golden share",
    "downgrade"
  ],
  "summary": "Research note arguing that after its partial IPO, Corvana Power & Light should trade with a lower beta to the sovereign, while remaining exposed to a sovereign downgrade through tariffs and state receivables.",
  "annotated_by": "LLM",
  "text": "\nThe partial IPO of Corvana Power & Light closed on 24 February 2026. The government sold down its stake from\n51% to 34%; a strategic investor now holds 25%. The government retains a golden share over tariff decisions.\n\nWe now expect CPL to trade with a beta of roughly 0.6 to the sovereign rather than ~0.9 previously. A sovereign\ndowngrade would still hit CPL via tariffs and receivables owed by state entities, but less than one-for-one.\n"
}
```

</details>

### 6. get_document(document_id=5)

<details><summary>result</summary>

```json
{
  "document_id": 5,
  "source_system": "ResearchHub",
  "source_file": "research/2026-06-10_bank-a_cnoc-update.md",
  "kind": "RESEARCH",
  "title": "CNOC - Production steady, guarantee structure unchanged",
  "publisher": "Bank A Research",
  "author": "EM Corporates",
  "published_at": "2026-06-10T00:00:00",
  "visibility": "external",
  "about_issuers": [
    "ISS-0001",
    "ISS-0002",
    "ISS-0007"
  ],
  "about_instruments": [],
  "about_curves": [],
  "about_currencies": [
    "USD"
  ],
  "topics": [
    "guarantee",
    "production",
    "ownership",
    "spreads",
    "sovereign curve"
  ],
  "summary": "Research note on Corvana National Oil Company (CNOC) saying Q1 output was steady, the state ownership and CNOC Finance B.V. guarantee structure for USD debt are unchanged, and its bonds trade 20-30bp wide of the sovereign curve.",
  "annotated_by": "LLM",
  "text": "\nCorvana Oil's output held at 410kb/d in Q1. The company remains 100% owned by the Ministry of Finance.\nCNOC Finance B.V. remains the issuing entity for all USD debt, with an unconditional guarantee from the parent.\nWe see CNOC bonds trading 20-30bp wide of the sovereign curve.\n"
}
```

</details>

### 7. get_document(document_id=9)

<details><summary>result</summary>

```json
{
  "document_id": 9,
  "source_system": "DeskNotes",
  "source_file": "desk_notes/em-credit-desk-notes.md",
  "kind": "DESK_NOTE",
  "title": null,
  "publisher": "EM Credit desk",
  "author": "dk",
  "published_at": "2026-02-11T09:14:00",
  "visibility": "credit_internal",
  "about_issuers": [
    "ISS-0001",
    "ISS-0005"
  ],
  "about_instruments": [],
  "about_curves": [],
  "about_currencies": [],
  "topics": [
    "sovereign proxy",
    "ownership",
    "spreads",
    "government stake"
  ],
  "summary": "A desk note reminding that CorTel trades as a sovereign proxy, moving with Corvana sovereign spreads despite the government's reduced 20% stake after the 2025 placement.",
  "annotated_by": "LLM",
  "text": "reminder CorTel trades as a sovereign proxy whatever the ownership says. govt stake is\nonly 20% now since the 2025 placement but it moves with CORVAN spreads."
}
```

</details>

### 8. get_document(document_id=10)

<details><summary>result</summary>

```json
{
  "document_id": 10,
  "source_system": "DeskNotes",
  "source_file": "desk_notes/em-credit-desk-notes.md",
  "kind": "DESK_NOTE",
  "title": null,
  "publisher": "EM Credit desk",
  "author": "js",
  "published_at": "2026-04-30T16:02:00",
  "visibility": "credit_internal",
  "about_issuers": [
    "ISS-0008"
  ],
  "about_instruments": [],
  "about_curves": [],
  "about_currencies": [],
  "topics": [
    "country of risk",
    "meridian mining",
    "data correction",
    "domicile"
  ],
  "summary": "A desk note saying Meridian Mining's country of risk should be Corvana because all its mines are there, even though it is UK listed and incorporated and the risk system still shows GB.",
  "annotated_by": "LLM",
  "text": "Meridian is UK listed / UK incorporated but every mine is in Corvana. Country of risk =\nCorvana for anything we do. risk system still has it as GB."
}
```

</details>

### 9. get_statements(entity_id='ISS-0003', predicate='OWNS', as_of=None)

<details><summary>result</summary>

```json
{
  "entity_id": "ISS-0003",
  "predicate": "OWNS",
  "as_of": "2026-10-27",
  "current": [
    {
      "statement_id": null,
      "edge_id": "ownership:3",
      "subject_type": "issuer",
      "subject_id": "ISS-0001",
      "predicate": "OWNS",
      "object_type": "issuer",
      "object_id": "ISS-0003",
      "value_num": "51.00",
      "value_text": "CPL annual report 2023",
      "holds": true,
      "as_of": "2023-12-31",
      "status": "REFERENCE",
      "method": null,
      "visibility": null,
      "tier": 2,
      "source_system": "OwnershipTracker",
      "source_file": "reference/ownership.csv",
      "document_title": null,
      "published_at": null,
      "quote": "Republic of Corvana (MinFin) -> Corvana Power & Light plc 51% (CPL annual report 2023)",
      "hidden_newer_count": 0
    },
    {
      "statement_id": 22,
      "edge_id": "stmt:22",
      "subject_type": "unresolved",
      "subject_id": "a strategic investor",
      "predicate": "OWNS",
      "object_type": "issuer",
      "object_id": "ISS-0003",
      "value_num": "25.0000",
      "value_text": null,
      "holds": true,
      "as_of": "2026-02-24",
      "status": "PROPOSED",
      "method": "MANUAL",
      "visibility": "credit_internal",
      "tier": 1,
      "source_system": "ResearchHub",
      "source_file": "research/2026-03-05_em-credit-internal_cpl-ipo.md",
      "document_title": "CPL post-IPO - partial decoupling from the sovereign",
      "published_at": "2026-03-05T00:00:00",
      "quote": "a strategic investor now holds 25%",
      "hidden_newer_count": 0
    }
  ],
  "other_sources": [
    {
      "statement_id": 21,
      "edge_id": "stmt:21",
      "subject_type": "issuer",
      "subject_id": "ISS-0001",
      "predicate": "OWNS",
      "object_type": "issuer",
      "object_id": "ISS-0003",
      "value_num": "34.0000",
      "value_text": "after partial IPO; golden share over tariff decisions retained",
      "holds": true,
      "as_of": "2026-02-24",
      "status": "PROPOSED",
      "method": "MANUAL",
      "visibility": "credit_internal",
      "tier": 1,
      "source_system": "ResearchHub",
      "source_file": "research/2026-03-05_em-credit-internal_cpl-ipo.md",
      "document_title": "CPL post-IPO - partial decoupling from the sovereign",
      "published_at": "2026-03-05T00:00:00",
      "quote": "The government sold down its stake from 51% to 34%",
      "hidden_newer_count": 0
    },
    {
      "statement_id": 17,
      "edge_id": "stmt:17",
      "subject_type": "issuer",
      "subject_id": "ISS-0001",
      "predicate": "OWNS",
      "object_type": "issuer",
      "object_id": "ISS-0003",
      "value_num": "51.0000",
      "value_text": null,
      "holds": true,
      "as_of": "2024-05-14",
      "status": "PROPOSED",
      "method": "MANUAL",
      "visibility": "external",
      "tier": 1,
      "source_system": "ResearchHub",
      "source_file": "research/2024-05-14_bank-a_corvana-sovereign-outlook.md",
      "document_title": "Corvana - Steady as she goes",
      "published_at": "2024-05-14T00:00:00",
      "quote": "Corvana Power & Light (51% state-owned) offers modest pick-up.",
      "hidden_newer_count": 0
    }
  ],
  "flags": [
    {
      "kind": "CORROBORATED",
      "subject": "issuer|ISS-0001|OWNS|ISS-0003",
      "edge_id": "ownership:3",
      "other_edge_id": "stmt:17",
      "message": "ISS-0001 OWNS ISS-0003: current 51 (REFERENCE, OwnershipTracker, as_of 2023-12-31) vs 51 (PROPOSED, ResearchHub, as_of 2024-05-14)"
    },
    {
      "kind": "STALE",
      "subject": "issuer|ISS-0001|OWNS|ISS-0003",
      "edge_id": "ownership:3",
      "other_edge_id": "stmt:21",
      "message": "ISS-0001 OWNS ISS-0003: current 51 (REFERENCE, OwnershipTracker, as_of 2023-12-31) vs 34 (PROPOSED, ResearchHub, as_of 2026-02-24)"
    }
  ],
  "hidden_newer_count": 0
}
```

</details>

### 10. get_statements(entity_id='ISS-0005', predicate='OWNS', as_of=None)

<details><summary>result</summary>

```json
{
  "entity_id": "ISS-0005",
  "predicate": "OWNS",
  "as_of": "2026-10-27",
  "current": [
    {
      "statement_id": 31,
      "edge_id": "stmt:31",
      "subject_type": "issuer",
      "subject_id": "ISS-0001",
      "predicate": "OWNS",
      "object_type": "issuer",
      "object_id": "ISS-0005",
      "value_num": "20.0000",
      "value_text": "since the 2025 placement",
      "holds": true,
      "as_of": "2026-02-11",
      "status": "PROPOSED",
      "method": "MANUAL",
      "visibility": "credit_internal",
      "tier": 1,
      "source_system": "DeskNotes",
      "source_file": "desk_notes/em-credit-desk-notes.md",
      "document_title": null,
      "published_at": "2026-02-11T09:14:00",
      "quote": "govt stake is only 20% now since the 2025 placement",
      "hidden_newer_count": 0
    }
  ],
  "other_sources": [
    {
      "statement_id": 13,
      "edge_id": "stmt:13",
      "subject_type": "issuer",
      "subject_id": "ISS-0001",
      "predicate": "OWNS",
      "object_type": "issuer",
      "object_id": "ISS-0005",
      "value_num": "35.0000",
      "value_text": "indirect, through a holding company",
      "holds": true,
      "as_of": "2023-10-02",
      "status": "PROPOSED",
      "method": "MANUAL",
      "visibility": "external",
      "tier": 1,
      "source_system": "ResearchHub",
      "source_file": "research/2023-10-02_bank-a_cortel-initiation.md",
      "document_title": "CorTel - Initiating coverage",
      "published_at": "2023-10-02T00:00:00",
      "quote": "Corvana Telecommunications (CorTel) is 35% owned by the state through a holding company.",
      "hidden_newer_count": 0
    }
  ],
  "flags": [
    {
      "kind": "SUPERSEDED",
      "subject": "issuer|ISS-0001|OWNS|ISS-0005",
      "edge_id": "stmt:31",
      "other_edge_id": "stmt:13",
      "message": "ISS-0001 OWNS ISS-0005: current 20 (PROPOSED, DeskNotes, as_of 2026-02-11) vs 35 (PROPOSED, ResearchHub, as_of 2023-10-02)"
    }
  ],
  "hidden_newer_count": 0
}
```

</details>

### 11. get_statements(entity_id='ISS-0008', predicate='COUNTRY_OF_RISK', as_of=None)

<details><summary>result</summary>

```json
{
  "entity_id": "ISS-0008",
  "predicate": "COUNTRY_OF_RISK",
  "as_of": "2026-10-27",
  "current": [
    {
      "statement_id": 10,
      "edge_id": "stmt:10",
      "subject_type": "issuer",
      "subject_id": "ISS-0008",
      "predicate": "COUNTRY_OF_RISK",
      "object_type": "country",
      "object_id": "GB",
      "value_num": null,
      "value_text": null,
      "holds": true,
      "as_of": "2026-04-30",
      "status": "INFERRED",
      "method": "RULE",
      "visibility": null,
      "tier": 3,
      "source_system": "SecMaster",
      "source_file": "reference/issuers.csv",
      "document_title": null,
      "published_at": null,
      "quote": "rule: country of risk defaults to country of incorporation (issuers.country_of_incorporation = GB)",
      "hidden_newer_count": 0
    }
  ],
  "other_sources": [
    {
      "statement_id": 32,
      "edge_id": "stmt:32",
      "subject_type": "issuer",
      "subject_id": "ISS-0008",
      "predicate": "COUNTRY_OF_RISK",
      "object_type": "country",
      "object_id": "QC",
      "value_num": null,
      "value_text": "UK incorporated but every mine is in Corvana; risk system still has GB",
      "holds": true,
      "as_of": "2026-04-30",
      "status": "PROPOSED",
      "method": "MANUAL",
      "visibility": "credit_internal",
      "tier": 1,
      "source_system": "DeskNotes",
      "source_file": "desk_notes/em-credit-desk-notes.md",
      "document_title": null,
      "published_at": "2026-04-30T16:02:00",
      "quote": "Country of risk = Corvana for anything we do.",
      "hidden_newer_count": 0
    }
  ],
  "flags": [
    {
      "kind": "CONFLICT",
      "subject": "issuer|ISS-0008|COUNTRY_OF_RISK|",
      "edge_id": "stmt:10",
      "other_edge_id": "stmt:32",
      "message": "ISS-0008 COUNTRY_OF_RISK GB: current GB (INFERRED, SecMaster, as_of 2026-04-30) vs QC (PROPOSED, DeskNotes, as_of 2026-04-30)"
    }
  ],
  "hidden_newer_count": 0
}
```

</details>

### 12. get_path(instrument_id='INS-1005', target_id='ISS-0001', channel_key='OWNS')

<details><summary>result</summary>

```json
{
  "key": "OWNS",
  "label": "state-owned (100% stake) via Corvana National Oil Company",
  "grade": "high",
  "hops": [
    {
      "from_node": "instrument:INS-1005",
      "predicate": "GUARANTEED_BY",
      "to_node": "issuer:ISS-0002",
      "grade": "high",
      "citations": [
        {
          "statement_id": null,
          "edge_id": "instruments:INS-1005:guarantor_id",
          "predicate": "GUARANTEED_BY",
          "source_system": "SecMaster",
          "source_file": "reference/instruments.csv",
          "document_title": null,
          "published_at": null,
          "as_of": "2026-10-27",
          "quote": "Corvana National Oil Co",
          "status": "INFERRED",
          "method": null,
          "visibility": null,
          "tier": 3
        }
      ]
    },
    {
      "from_node": "issuer:ISS-0002",
      "predicate": "OWNS",
      "to_node": "issuer:ISS-0001",
      "grade": "high",
      "citations": [
        {
          "statement_id": null,
          "edge_id": "ownership:1",
          "predicate": "OWNS",
          "source_system": "OwnershipTracker",
          "source_file": "reference/ownership.csv",
          "document_title": null,
          "published_at": null,
          "as_of": "2020-06-30",
          "quote": "Republic of Corvana (MinFin) -> Corvana National Oil Company 100% (Annual report 2019)",
          "status": "REFERENCE",
          "method": null,
          "visibility": null,
          "tier": 2
        },
        {
          "statement_id": 15,
          "edge_id": "stmt:15",
          "predicate": "OWNS",
          "source_system": "ResearchHub",
          "source_file": "research/2024-05-14_bank-a_corvana-sovereign-outlook.md",
          "document_title": "Corvana - Steady as she goes",
          "published_at": "2024-05-14T00:00:00",
          "as_of": "2024-05-14",
          "quote": "CNOC remains wholly state-owned",
          "status": "PROPOSED",
          "method": "MANUAL",
          "visibility": "external",
          "tier": 1
        },
        {
          "statement_id": 24,
          "edge_id": "stmt:24",
          "predicate": "OWNS",
          "source_system": "ResearchHub",
          "source_file": "research/2026-06-10_bank-a_cnoc-update.md",
          "document_title": "CNOC - Production steady, guarantee structure unchanged",
          "published_at": "2026-06-10T00:00:00",
          "as_of": "2026-06-10",
          "quote": "The company remains 100% owned by the Ministry of Finance.",
          "status": "PROPOSED",
          "method": "MANUAL",
          "visibility": "external",
          "tier": 1
        }
      ]
    }
  ],
  "paths_considered": 4,
  "user": "bob",
  "as_of": "2026-10-27",
  "instrument_id": "INS-1005",
  "target_id": "ISS-0001"
}
```

</details>

## Answer

Corvana is rated BB- by Agency A, and the outlook was cut from Stable to Negative on 2026-09-18. Five of your resolved positions are exposed to a downgrade, a sixth may be, and two holdings couldn't be identified. One thing changes how to read this: the 5Y CDS shows as −20m, but the system doesn't record whether that sign means you bought or sold protection. So I can't tell you whether it offsets the bonds or adds to them. Please check it in the order management system (OMS).

**Exposed (confirmed)**

1. **CNOC Finance 5.875% 2029, USD 12m.** This is the strongest link. The bond is guaranteed by Corvana National Oil Company (inferred from the security master) [instruments:INS-1005:guarantor_id], and the state owns 100% of that company [ownership:1]. Two Bank A notes back this up [stmt 15] [stmt 24], and the second says [doc 5: "The company remains 100% owned by the Ministry of Finance"]. CNOC's country of risk is Corvana [stmt:4] [country:QC:sovereign_issuer_id]. Two weaker links: its rating is capped at the sovereign [stmt:27], and it trades as a sovereign proxy [stmt:16]. Research says CNOC bonds trade [doc 5: "20-30bp wide of the sovereign curve"], and Bank B says of a downgrade [doc 8: "Expect a one-for-one move."]
2. **Corvana Development Bank 4.75% 2027, USD 6m.** The sovereign guarantees it directly [instruments:INS-1007:guarantor_id]. The current record of that guarantee is inferred, and three research or desk sources agree. The state also owns 100% [ownership:2], and the country of risk is Corvana [stmt:6]. Bank B: [doc 8: "CDB - explicitly guaranteed, will move with the sovereign."] Desk note: [doc 11: "CDB 27s are guaranteed so treat like sovereign."]
3. **Corvana 5Y senior CDS, −USD 20m.** This contract references the sovereign directly [instruments:INS-2001:issuer_id]. Bank B [doc 8: "We recommend buying 5Y CDS protection on the sovereign."] As noted above, I can't confirm which side you're on.
4. **Corvana Power & Light 6% 2031, USD 7.5m.** The reference data shows a 51% state stake [ownership:3], but that figure dates from 2023-12-31 and is flagged as **stale**. Internal research reports that after the IPO [doc 4: "The government sold down its stake from 51% to 34%"] [stmt 21] (research only, unconfirmed), and the state kept a golden share over tariffs. The country of risk is Corvana [stmt:5]. There's also a spread beta of 0.6 to the sovereign [stmt:23], a weaker link. Research expects [doc 4: "A sovereign downgrade would still hit CPL via tariffs and receivables owed by state entities, but less than one-for-one."] Desk: [doc 11: "CPL less so now post IPO."]
5. **CorTel 5.5% 2032, USD 9m.** The state stake is 20% [stmt 31], which is research only, unconfirmed. That figure replaces the 35% in a 2023 note [stmt 13]. The bond also trades as a sovereign proxy [stmt:30] (weak link), and the country of risk is Corvana [stmt:7]. Desk: [doc 9: "CorTel trades as a sovereign proxy whatever the ownership says"], [doc 9: "it moves with CORVAN spreads"]. The 2023 initiation note on CorTel is older than both of these desk views.

**Possibly exposed (unconfirmed)**

6. **Meridian Mining 7% 2030, USD 4m.** The sources conflict. The current record puts its country of risk in Great Britain, inferred from where it is incorporated [stmt 10]. A desk note says it should be Corvana (research only, unconfirmed) [stmt 32]: [doc 10: "every mine is in Corvana"], [doc 10: "risk system still has it as GB."]

**Unresolved: neither exposed nor safe**
- **XS2812345672, USD 10m.** "Matches no instrument known on 2026-10-27; nearest known ISIN XS2812345671 (INS-1001); not applied."
- **XS2999887768, USD 5m.** "Matches no instrument known on 2026-10-27."

**What the research says overall**
Bank B gives [doc 8: "~60% probability of a one-notch downgrade to B+ within six months"] and names [doc 8: "Fiscal slippage from energy subsidies"] as the main driver. Across the notes, the pattern is:
- **Moves with the sovereign:** CNOC and CDB.
- **Moves less:** CPL.
- **Proxy despite the small stake:** CorTel.
- **Flagged by the desk, not the system:** Meridian.

Bank A's 2024 stable view (doc 2) came before the outlook change. Bank B's note on Valdoria (doc 3) isn't about any position you hold, so I didn't use either one.

# Agent transcript: bob, as of 2026-10-28

Model: claude-opus-5-5

## Question

Corvana was downgraded to B+ yesterday. What in my book is exposed, how, and what does our research say about it?

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
  "as_of": "2026-10-28",
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
      "rating": "B+",
      "outlook": "Stable",
      "action_date": "2026-10-28",
      "rank": 14
    },
    "history": [
      {
        "agency": "Agency A",
        "rating": "B+",
        "outlook": "Stable",
        "action_date": "2026-10-28",
        "rank": 14
      },
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
      "rating": "B+",
      "outlook": "Stable",
      "action_date": "2026-10-28",
      "rank": 14
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
        },
        {
          "kind": "RATING_LAG",
          "message": "ISS-0004 rated BB- (rank 13) is better than guarantor ISS-0001 rated B+ (rank 14)"
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
    },
    {
      "position": {
        "book": "EM_CREDIT",
        "instrument_ref": "XS2999887768",
        "ref_type": "ISIN",
        "quantity": "5000000.00",
        "notional_ccy": "USD",
        "as_of_date": "2026-10-27",
        "instrument_id": "INS-1012",
        "description": "CNOC Finance 6.75% 2034",
        "instrument_type": "Corporate Bond",
        "resolution_note": "resolved by ISIN"
      },
      "exposed": "yes",
      "channels": [
        {
          "key": "OWNS",
          "label": "state-owned (100% stake) via Corvana National Oil Company",
          "grade": "high",
          "hop_count": 2,
          "edge_ids": [
            "instruments:INS-1012:guarantor_id",
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
            "instruments:INS-1012:guarantor_id",
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
            "instruments:INS-1012:guarantor_id",
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
            "instruments:INS-1012:guarantor_id",
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
      "flag_message": "position EM_CREDIT/XS2812345672 (ISIN) matches no instrument known on 2026-10-28; nearest known ISIN XS2812345671 (INS-1001); not applied"
    }
  ],
  "research": [
    {
      "document_id": 13,
      "title": "Corvana cut to B+ - what next",
      "publisher": "Bank B Research",
      "published_at": "2026-10-28T00:00:00",
      "visibility": "external",
      "summary": "A research note on Agency A's downgrade of the Republic of Corvana to B+ and expected knock-on rating actions for CNOC, Corvana Development Bank and Corvana Telecommunications.",
      "topics": [
        "downgrade",
        "guarantee",
        "sovereign rating",
        "government ownership",
        "standalone assessment"
      ],
      "about_on_path": [
        "ISS-0001",
        "ISS-0002",
        "ISS-0004",
        "ISS-0005"
      ]
    },
    {
      "document_id": 2,
      "title": "Corvana - Steady as she goes",
      "publisher": "Bank A Research",
      "published_at": "2024-05-14T00:00:00",
      "visibility": "external",
      "summary": null,
      "topics": [],
      "about_on_path": [
        "ISS-0001",
        "ISS-0002",
        "ISS-0003",
        "ISS-0004"
      ]
    },
    {
      "document_id": 8,
      "title": "Republic of Corvana - Outlook to Negative; downgrade risk rising",
      "publisher": "Bank B Research",
      "published_at": "2026-09-22T00:00:00",
      "visibility": "external",
      "summary": null,
      "topics": [],
      "about_on_path": [
        "ISS-0001",
        "ISS-0002",
        "ISS-0004"
      ]
    },
    {
      "document_id": 11,
      "title": null,
      "publisher": "EM Credit desk",
      "published_at": "2026-09-19T08:40:00",
      "visibility": "credit_internal",
      "summary": null,
      "topics": [],
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
      "summary": null,
      "topics": [],
      "about_on_path": [
        "ISS-0001",
        "ISS-0002"
      ]
    },
    {
      "document_id": 10,
      "title": null,
      "publisher": "EM Credit desk",
      "published_at": "2026-04-30T16:02:00",
      "visibility": "credit_internal",
      "summary": null,
      "topics": [],
      "about_on_path": [
        "ISS-0001",
        "ISS-0008"
      ]
    },
    {
      "document_id": 9,
      "title": null,
      "publisher": "EM Credit desk",
      "published_at": "2026-02-11T09:14:00",
      "visibility": "credit_internal",
      "summary": null,
      "topics": [],
      "about_on_path": [
        "ISS-0001",
        "ISS-0005"
      ]
    },
    {
      "document_id": 4,
      "title": "CPL post-IPO - partial decoupling from the sovereign",
      "publisher": "Internal - EM Credit",
      "published_at": "2026-03-05T00:00:00",
      "visibility": "credit_internal",
      "summary": null,
      "topics": [],
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
      "summary": null,
      "topics": [],
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
      "summary": null,
      "topics": [],
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

### 3. get_document(document_id=13)

<details><summary>result</summary>

```json
{
  "document_id": 13,
  "source_system": "ResearchHub",
  "source_file": "updates/2026-10-28/research/2026-10-28_bank-b_corvana-downgrade.md",
  "kind": "RESEARCH",
  "title": "Corvana cut to B+ - what next",
  "publisher": "Bank B Research",
  "author": "CEEMEA Credit Strategy",
  "published_at": "2026-10-28T00:00:00",
  "visibility": "external",
  "about_issuers": [
    "ISS-0001",
    "ISS-0002",
    "ISS-0004",
    "ISS-0005"
  ],
  "about_instruments": [],
  "about_curves": [],
  "about_currencies": [],
  "topics": [
    "downgrade",
    "guarantee",
    "sovereign rating",
    "government ownership",
    "standalone assessment"
  ],
  "summary": "A research note on Agency A's downgrade of the Republic of Corvana to B+ and expected knock-on rating actions for CNOC, Corvana Development Bank and Corvana Telecommunications.",
  "annotated_by": "LLM",
  "text": "\nAgency A downgraded the Republic of Corvana to B+ (outlook Stable) this morning; CNOC followed as expected.\nCorvana Development Bank has not yet been actioned, which we find inconsistent given its explicit guarantee -\nwe expect it to follow within days.\n\nWe note the government's stake in Corvana Telecommunications is now 20% following last year's placement,\nconfirming our view that CorTel should be assessed more on a standalone basis - although in practice its bonds\nhave continued to trade with the sovereign.\n"
}
```

</details>

### 4. get_document(document_id=8)

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
    "ISS-0009"
  ],
  "about_instruments": [],
  "about_curves": [],
  "about_currencies": [
    "USD"
  ],
  "topics": [],
  "summary": null,
  "annotated_by": "RULE",
  "text": "\nFollowing Agency A's revision of the outlook to Negative on 18 September, we see a ~60% probability of a\none-notch downgrade to B+ within six months. Fiscal slippage from energy subsidies is the main driver.\n\nRead-across:\n- Corvana Oil (CNOC) - rating capped at the sovereign; USD bonds issued via its Dutch finance subsidiary carry\n  a full parent guarantee. Expect a one-for-one move.\n- CDB - explicitly guaranteed, will move with the sovereign.\n- First Corvana Bank - roughly 28% of assets in government securities; the sovereign-bank nexus means FCB is\n  exposed despite being privately owned.\n- Republic of Valdoria - limited direct trade linkage, but EM sovereign funds often hold both; some spillover\n  likely.\n\nWe recommend buying 5Y CDS protection on the sovereign.\n"
}
```

</details>

### 5. get_document(document_id=11)

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
  "topics": [],
  "summary": null,
  "annotated_by": "RULE",
  "text": "after the outlook change - remember CDB 27s are guaranteed so treat like sovereign.\nCPL less so now post IPO."
}
```

</details>

### 6. get_document(document_id=4)

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
  "topics": [],
  "summary": null,
  "annotated_by": "RULE",
  "text": "\nThe partial IPO of Corvana Power & Light closed on 24 February 2026. The government sold down its stake from\n51% to 34%; a strategic investor now holds 25%. The government retains a golden share over tariff decisions.\n\nWe now expect CPL to trade with a beta of roughly 0.6 to the sovereign rather than ~0.9 previously. A sovereign\ndowngrade would still hit CPL via tariffs and receivables owed by state entities, but less than one-for-one.\n"
}
```

</details>

### 7. get_document(document_id=10)

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
    "ISS-0001",
    "ISS-0008"
  ],
  "about_instruments": [],
  "about_curves": [],
  "about_currencies": [],
  "topics": [],
  "summary": null,
  "annotated_by": "RULE",
  "text": "Meridian is UK listed / UK incorporated but every mine is in Corvana. Country of risk =\nCorvana for anything we do. risk system still has it as GB."
}
```

</details>

### 8. get_document(document_id=9)

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
  "topics": [],
  "summary": null,
  "annotated_by": "RULE",
  "text": "reminder CorTel trades as a sovereign proxy whatever the ownership says. govt stake is\nonly 20% now since the 2025 placement but it moves with CORVAN spreads."
}
```

</details>

### 9. get_document(document_id=5)

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
  "topics": [],
  "summary": null,
  "annotated_by": "RULE",
  "text": "\nCorvana Oil's output held at 410kb/d in Q1. The company remains 100% owned by the Ministry of Finance.\nCNOC Finance B.V. remains the issuing entity for all USD debt, with an unconditional guarantee from the parent.\nWe see CNOC bonds trading 20-30bp wide of the sovereign curve.\n"
}
```

</details>

### 10. get_statements(entity_id='ISS-0003', predicate='OWNS', as_of=None)

<details><summary>result</summary>

```json
{
  "entity_id": "ISS-0003",
  "predicate": "OWNS",
  "as_of": "2026-10-28",
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

### 11. get_statements(entity_id='ISS-0005', predicate='OWNS', as_of=None)

<details><summary>result</summary>

```json
{
  "entity_id": "ISS-0005",
  "predicate": "OWNS",
  "as_of": "2026-10-28",
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

### 12. get_statements(entity_id='ISS-0008', predicate='COUNTRY_OF_RISK', as_of=None)

<details><summary>result</summary>

```json
{
  "entity_id": "ISS-0008",
  "predicate": "COUNTRY_OF_RISK",
  "as_of": "2026-10-28",
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

### 13. get_path(instrument_id='INS-1005', target_id='ISS-0001', channel_key='OWNS')

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
  "as_of": "2026-10-28",
  "instrument_id": "INS-1005",
  "target_id": "ISS-0001"
}
```

</details>

### 14. get_statements(entity_id='ISS-0004', predicate='GUARANTEED_BY', as_of=None)

<details><summary>result</summary>

```json
{
  "entity_id": "ISS-0004",
  "predicate": "GUARANTEED_BY",
  "as_of": "2026-10-28",
  "current": [
    {
      "statement_id": 1,
      "edge_id": "stmt:1",
      "subject_type": "issuer",
      "subject_id": "ISS-0004",
      "predicate": "GUARANTEED_BY",
      "object_type": "issuer",
      "object_id": "ISS-0001",
      "value_num": null,
      "value_text": "Explicit sovereign guarantee on senior debt",
      "holds": true,
      "as_of": "2022-12-31",
      "status": "INFERRED",
      "method": "RULE",
      "visibility": null,
      "tier": 2,
      "source_system": "OwnershipTracker",
      "source_file": "reference/ownership.csv",
      "document_title": null,
      "published_at": null,
      "quote": "Explicit sovereign guarantee on senior debt",
      "hidden_newer_count": 0
    }
  ],
  "other_sources": [
    {
      "statement_id": 29,
      "edge_id": "stmt:29",
      "subject_type": "issuer",
      "subject_id": "ISS-0004",
      "predicate": "GUARANTEED_BY",
      "object_type": "issuer",
      "object_id": "ISS-0001",
      "value_num": null,
      "value_text": "explicit",
      "holds": true,
      "as_of": "2026-09-22",
      "status": "PROPOSED",
      "method": "MANUAL",
      "visibility": "external",
      "tier": 1,
      "source_system": "ResearchHub",
      "source_file": "research/2026-09-22_bank-b_corvana-negative-watch.md",
      "document_title": "Republic of Corvana - Outlook to Negative; downgrade risk rising",
      "published_at": "2026-09-22T00:00:00",
      "quote": "CDB - explicitly guaranteed, will move with the sovereign.",
      "hidden_newer_count": 0
    },
    {
      "statement_id": 33,
      "edge_id": "stmt:33",
      "subject_type": "issuer",
      "subject_id": "ISS-0004",
      "predicate": "GUARANTEED_BY",
      "object_type": "issuer",
      "object_id": "ISS-0001",
      "value_num": null,
      "value_text": "treat like sovereign",
      "holds": true,
      "as_of": "2026-09-19",
      "status": "PROPOSED",
      "method": "MANUAL",
      "visibility": "credit_internal",
      "tier": 1,
      "source_system": "DeskNotes",
      "source_file": "desk_notes/em-credit-desk-notes.md",
      "document_title": null,
      "published_at": "2026-09-19T08:40:00",
      "quote": "CDB 27s are guaranteed so treat like sovereign",
      "hidden_newer_count": 0
    },
    {
      "statement_id": 18,
      "edge_id": "stmt:18",
      "subject_type": "issuer",
      "subject_id": "ISS-0004",
      "predicate": "GUARANTEED_BY",
      "object_type": "issuer",
      "object_id": "ISS-0001",
      "value_num": null,
      "value_text": "explicit",
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
      "quote": "Corvana Development Bank benefits from an explicit guarantee and should be treated as sovereign risk.",
      "hidden_newer_count": 0
    }
  ],
  "flags": [
    {
      "kind": "CORROBORATED",
      "subject": "issuer|ISS-0004|GUARANTEED_BY|ISS-0001",
      "edge_id": "stmt:1",
      "other_edge_id": "stmt:18",
      "message": "ISS-0004 GUARANTEED_BY ISS-0001: current true (INFERRED, OwnershipTracker, as_of 2022-12-31) vs true (PROPOSED, ResearchHub, as_of 2024-05-14)"
    },
    {
      "kind": "CORROBORATED",
      "subject": "issuer|ISS-0004|GUARANTEED_BY|ISS-0001",
      "edge_id": "stmt:1",
      "other_edge_id": "stmt:29",
      "message": "ISS-0004 GUARANTEED_BY ISS-0001: current true (INFERRED, OwnershipTracker, as_of 2022-12-31) vs true (PROPOSED, ResearchHub, as_of 2026-09-22)"
    },
    {
      "kind": "CORROBORATED",
      "subject": "issuer|ISS-0004|GUARANTEED_BY|ISS-0001",
      "edge_id": "stmt:1",
      "other_edge_id": "stmt:33",
      "message": "ISS-0004 GUARANTEED_BY ISS-0001: current true (INFERRED, OwnershipTracker, as_of 2022-12-31) vs true (PROPOSED, DeskNotes, as_of 2026-09-19)"
    }
  ],
  "hidden_newer_count": 0
}
```

</details>

### 15. get_path(instrument_id='INS-1008', target_id='ISS-0001', channel_key='TRADES_AS_PROXY_FOR')

<details><summary>result</summary>

```json
{
  "key": "TRADES_AS_PROXY_FOR",
  "label": "trades as a sovereign proxy",
  "grade": "low",
  "hops": [
    {
      "from_node": "instrument:INS-1008",
      "predicate": "ISSUED_BY",
      "to_node": "issuer:ISS-0005",
      "grade": "high",
      "citations": [
        {
          "statement_id": null,
          "edge_id": "instruments:INS-1008:issuer_id",
          "predicate": "ISSUED_BY",
          "source_system": "SecMaster",
          "source_file": "reference/instruments.csv",
          "document_title": null,
          "published_at": null,
          "as_of": "2026-10-27",
          "quote": "Corvana Telecommunications",
          "status": "INFERRED",
          "method": null,
          "visibility": null,
          "tier": 3
        }
      ]
    },
    {
      "from_node": "issuer:ISS-0005",
      "predicate": "TRADES_AS_PROXY_FOR",
      "to_node": "issuer:ISS-0001",
      "grade": "low",
      "citations": [
        {
          "statement_id": 30,
          "edge_id": "stmt:30",
          "predicate": "TRADES_AS_PROXY_FOR",
          "source_system": "DeskNotes",
          "source_file": "desk_notes/em-credit-desk-notes.md",
          "document_title": null,
          "published_at": "2026-02-11T09:14:00",
          "as_of": "2026-02-11",
          "quote": "CorTel trades as a sovereign proxy whatever the ownership says",
          "status": "PROPOSED",
          "method": "MANUAL",
          "visibility": "credit_internal",
          "tier": 1
        }
      ]
    }
  ],
  "paths_considered": 1,
  "user": "bob",
  "as_of": "2026-10-28",
  "instrument_id": "INS-1008",
  "target_id": "ISS-0001"
}
```

</details>

## Answer

Six of your seven EM_CREDIT holdings are tied to Corvana: five are confirmed, one is unconfirmed, and one ISIN couldn't be identified at all. The tightest links are the CNOC bonds, the CDB bond and the sovereign CDS. One correction on timing: the rating history shows Agency A's cut to B+ (outlook Stable, from BB-/Negative) dated **2026-10-28**, which is today, not yesterday. Bank B's note on it is also dated today.

## Confirmed exposure

| Position | Notional | How it's linked to Corvana |
|---|---|---|
| CNOC Finance 5.875% 2029 (INS-1005) | USD 12.0m | Guaranteed by Corvana National Oil Company (CNOC), which is 100% state-owned [instruments:INS-1005:guarantor_id] [ownership:1] |
| CNOC Finance 6.75% 2034 (INS-1012) | USD 5.0m | Same structure [instruments:INS-1012:guarantor_id] [ownership:1] |
| Corvana Development Bank (CDB) 4.75% 2027 (INS-1007) | USD 6.0m | Guaranteed by the Republic [instruments:INS-1007:guarantor_id]; 100% state-owned [ownership:2] |
| Corvana 5Y senior CDS (INS-2001) | USD -20.0m | The CDS references the sovereign directly [instruments:INS-2001:issuer_id] |
| Corvana Power & Light (CPL) 6% 2031 (INS-1006) | USD 7.5m | Recorded as 51% state-owned [ownership:3] |
| CorTel 5.5% 2032 (INS-1008) | USD 9.0m | 20% state stake [stmt 31]; trades as a sovereign proxy [stmt 30] |

**CNOC bonds:** CNOC's 100% state ownership is backed by the ownership tracker and two research notes [stmt 15] [stmt 24], and Bank A wrote that "The company remains 100% owned by the Ministry of Finance" [doc 5: "unconditional guarantee from the parent"]. Two further links are research only, unconfirmed: a rating cap at the sovereign [stmt 27] and trading as a sovereign proxy [stmt 16]. Country of risk is Corvana [stmt 4].

**CDB 2027:** the sovereign guarantee on CDB is inferred [stmt 1]. Three research and desk sources agree with it [stmt 18] [stmt 29] [stmt 33]. Country of risk is Corvana [stmt 6].

**Corvana CDS:** the sign convention for derivatives is undocumented, so the -20m is shown as it appears in the order management system. I can't confirm whether it is bought or sold protection.

**CPL 2031:** the 51% stake comes from the 2023 annual report and is **flagged stale** [ownership:3]. Internal research (research only, unconfirmed) says the state cut its stake to 34% in the February 2026 IPO [stmt 21] [doc 4: "The government sold down its stake from 51% to 34%"]. A 0.6 spread beta to the sovereign is also research only, unconfirmed [stmt 23]. Country of risk is Corvana [stmt 5].

**CorTel 2032:** both the 20% stake and the proxy link come from a desk note and are research only, unconfirmed. They replace an older 35% / not-a-proxy view [stmt 13]. Country of risk is Corvana [stmt 7].

## Unconfirmed exposure
- **Meridian Mining 7% 2030 (INS-1009), USD 4.0m.** Country of risk is inferred as GB from where it is incorporated [stmt 10]. A desk note puts it as Corvana instead (research only, unconfirmed) [stmt 32] [doc 10: "every mine is in Corvana. Country of risk =
Corvana for anything we do. risk system still has it as GB"]. The two sources conflict.

## Unresolved holding (counts as neither exposed nor safe)
- **XS2812345672, USD 10.0m.** Flag message: "matches no instrument known on 2026-10-28; nearest known ISIN XS2812345671 (INS-1001); not applied". Worth checking whether this is a typo in the ISIN.

## What the research says
- **Bank B, today (doc 13):** CNOC has already been cut: [doc 13: "CNOC followed as expected"]. CDB hasn't been, and Bank B calls that [doc 13: "inconsistent given its explicit guarantee"], adding [doc 13: "we expect it to follow within days"]. The data shows the same lag: CDB is still BB-, above its B+ guarantor. On CorTel, Bank B says the stake [doc 13: "is now 20% following last year's placement"] and that CorTel [doc 13: "should be assessed more on a standalone basis"], [doc 13: "although in practice its bonds
have continued to trade with the sovereign"].
- **Bank B, 22 Sep (doc 8):** this note predicted the cut [doc 8: "~60% probability of a
one-notch downgrade to B+ within six months"], expected CNOC to move [doc 8: "Expect a one-for-one move"] and CDB to [doc 8: "will move with the sovereign"]. Its recommendation was [doc 8: "buying 5Y CDS protection on the sovereign"].
- **CPL (doc 4, internal):** beta is now [doc 4: "roughly 0.6 to the sovereign rather than ~0.9 previously"]. A downgrade would still hit CPL [doc 4: "but less than one-for-one"].
- **Desk notes:** on CDB, [doc 11: "CDB 27s are guaranteed so treat like sovereign"] and [doc 11: "CPL less so now post IPO"]. On CorTel, [doc 9: "it moves with CORVAN spreads"].

## Bottom line
- **Expect roughly sovereign-like moves:** CNOC (17m in total) and CDB (6m, where a downgrade is still to come).
- **Less than one-for-one:** CPL (7.5m). Its state stake in our records is out of date.
- **Moves with the sovereign in practice, despite only a 20% state stake:** CorTel (9m).
- **Depends on treatment:** Meridian (4m) is only exposed if you use the desk's Corvana country-of-risk view rather than the GB default.
- **Two things to check:** the direction of the CDS position and the unidentified 10m ISIN.

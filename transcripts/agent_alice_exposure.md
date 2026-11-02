# Agent transcript: alice, as of 2026-10-27

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
  "user": "alice",
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
        "book": "EM_MACRO",
        "instrument_ref": "CVD IRS 5Y",
        "ref_type": "TICKER",
        "quantity": "800000000.00",
        "notional_ccy": "CVD",
        "as_of_date": "2026-10-27",
        "instrument_id": "INS-2003",
        "description": "CVD 5Y pay-fixed interest rate swap",
        "instrument_type": "Interest Rate Swap",
        "resolution_note": "resolved by TICKER"
      },
      "exposed": "yes",
      "channels": [
        {
          "key": "PRICED_OFF>DENOMINATED_IN>CURRENCY_OF>SOVEREIGN_IS",
          "label": "priced off the sovereign's rates curve",
          "grade": "high",
          "hop_count": 4,
          "edge_ids": [
            "instruments:INS-2003:underlying_curve",
            "curves:CVD-OIS:currency",
            "country:QC:currency",
            "country:QC:sovereign_issuer_id"
          ],
          "paths_considered": 1
        },
        {
          "key": "DENOMINATED_IN>CURRENCY_OF>SOVEREIGN_IS",
          "label": "denominated in the sovereign's currency",
          "grade": "high",
          "hop_count": 3,
          "edge_ids": [
            "instruments:INS-2003:currency",
            "country:QC:currency",
            "country:QC:sovereign_issuer_id"
          ],
          "paths_considered": 1
        }
      ],
      "flags": []
    },
    {
      "position": {
        "book": "EM_MACRO",
        "instrument_ref": "GB00NB123454",
        "ref_type": "ISIN",
        "quantity": "5000000.00",
        "notional_ccy": "GBP",
        "as_of_date": "2026-10-27",
        "instrument_id": "INS-1011",
        "description": "Northbridge Retail 4.25% 2029",
        "instrument_type": "Corporate Bond",
        "resolution_note": "resolved by ISIN"
      },
      "exposed": "no",
      "channels": [],
      "flags": []
    },
    {
      "position": {
        "book": "EM_MACRO",
        "instrument_ref": "INS-2002",
        "ref_type": "INTERNAL",
        "quantity": "25000000.00",
        "notional_ccy": "USD",
        "as_of_date": "2026-10-27",
        "instrument_id": "INS-2002",
        "description": "USD/CVD 3M non-deliverable forward",
        "instrument_type": "FX Forward",
        "resolution_note": "resolved by INTERNAL"
      },
      "exposed": "yes",
      "channels": [
        {
          "key": "DENOMINATED_IN>CURRENCY_OF>SOVEREIGN_IS",
          "label": "denominated in the sovereign's currency",
          "grade": "high",
          "hop_count": 3,
          "edge_ids": [
            "instruments:INS-2002:currency",
            "country:QC:currency",
            "country:QC:sovereign_issuer_id"
          ],
          "paths_considered": 1
        }
      ],
      "flags": []
    },
    {
      "position": {
        "book": "EM_MACRO",
        "instrument_ref": "QC000CV33031",
        "ref_type": "ISIN",
        "quantity": "450000000.00",
        "notional_ccy": "CVD",
        "as_of_date": "2026-10-27",
        "instrument_id": "INS-1004",
        "description": "Corvana Government Bond 10.5% 2033",
        "instrument_type": "Sovereign Bond",
        "resolution_note": "resolved by ISIN"
      },
      "exposed": "yes",
      "channels": [
        {
          "key": "ISSUED_BY",
          "label": "issued by the sovereign",
          "grade": "high",
          "hop_count": 1,
          "edge_ids": [
            "instruments:INS-1004:issuer_id"
          ],
          "paths_considered": 1
        },
        {
          "key": "PRICED_OFF>DENOMINATED_IN>CURRENCY_OF>SOVEREIGN_IS",
          "label": "priced off the sovereign's rates curve",
          "grade": "high",
          "hop_count": 4,
          "edge_ids": [
            "instruments:INS-1004:underlying_curve",
            "curves:CVD-GOVT:currency",
            "country:QC:currency",
            "country:QC:sovereign_issuer_id"
          ],
          "paths_considered": 1
        },
        {
          "key": "DENOMINATED_IN>CURRENCY_OF>SOVEREIGN_IS",
          "label": "denominated in the sovereign's currency",
          "grade": "high",
          "hop_count": 3,
          "edge_ids": [
            "instruments:INS-1004:currency",
            "country:QC:currency",
            "country:QC:sovereign_issuer_id"
          ],
          "paths_considered": 1
        }
      ],
      "flags": []
    },
    {
      "position": {
        "book": "EM_MACRO",
        "instrument_ref": "XS2812345671",
        "ref_type": "ISIN",
        "quantity": "15000000.00",
        "notional_ccy": "USD",
        "as_of_date": "2026-10-27",
        "instrument_id": "INS-1001",
        "description": "Republic of Corvana 6.5% 2030",
        "instrument_type": "Sovereign Bond",
        "resolution_note": "resolved by ISIN"
      },
      "exposed": "yes",
      "channels": [
        {
          "key": "ISSUED_BY",
          "label": "issued by the sovereign",
          "grade": "high",
          "hop_count": 1,
          "edge_ids": [
            "instruments:INS-1001:issuer_id"
          ],
          "paths_considered": 1
        }
      ],
      "flags": []
    },
    {
      "position": {
        "book": "EM_MACRO",
        "instrument_ref": "XS2900123451",
        "ref_type": "ISIN",
        "quantity": "8000000.00",
        "notional_ccy": "USD",
        "as_of_date": "2026-10-27",
        "instrument_id": "INS-1010",
        "description": "Republic of Valdoria 8% 2031",
        "instrument_type": "Sovereign Bond",
        "resolution_note": "resolved by ISIN"
      },
      "exposed": "unconfirmed",
      "channels": [
        {
          "key": "CORRELATED_WITH",
          "label": "correlation 0.7 with the sovereign",
          "grade": "low",
          "hop_count": 2,
          "edge_ids": [
            "instruments:INS-1010:issuer_id",
            "stmt:20"
          ],
          "paths_considered": 1
        }
      ],
      "flags": []
    }
  ],
  "unresolved": [],
  "research": [
    {
      "document_id": 7,
      "title": "CVD - reserves under pressure",
      "publisher": "Internal - EM Macro",
      "published_at": "2026-08-21T00:00:00",
      "visibility": "macro_internal",
      "summary": "EM macro note arguing Corvana's falling FX reserves will pressure the dinar, favouring long USD/CVD via NDFs and paying CVD 5Y swaps to hedge a possible sovereign downgrade and local bond outflows.",
      "topics": [
        "fx reserves",
        "downgrade",
        "usd/cvd",
        "ndf",
        "rates hedge"
      ],
      "about_on_path": [
        "CVD",
        "CVD-GOVT",
        "INS-1004",
        "INS-2002",
        "INS-2003",
        "ISS-0001"
      ]
    },
    {
      "document_id": 8,
      "title": "Republic of Corvana - Outlook to Negative; downgrade risk rising",
      "publisher": "Bank B Research",
      "published_at": "2026-09-22T00:00:00",
      "visibility": "external",
      "summary": "Research note arguing that Agency A's negative outlook on the Republic of Corvana raises downgrade risk and assessing read-across to related issuers and Valdoria, recommending buying 5Y CDS protection.",
      "topics": [
        "outlook negative",
        "downgrade risk",
        "sovereign-bank nexus",
        "guarantee",
        "cds"
      ],
      "about_on_path": [
        "ISS-0001",
        "ISS-0009"
      ]
    },
    {
      "document_id": 3,
      "title": "Valdoria - Neighbour risk overstated",
      "publisher": "Bank B Research",
      "published_at": "2025-11-18T00:00:00",
      "visibility": "external",
      "summary": "A research note arguing that Valdoria's use as a trading proxy for Corvana overstates the neighbour risk, since bilateral trade is small even though 5Y CDS correlation rises in risk-off episodes.",
      "topics": [
        "proxy",
        "contagion",
        "correlation",
        "cds",
        "trade linkages"
      ],
      "about_on_path": [
        "ISS-0001",
        "ISS-0009"
      ]
    },
    {
      "document_id": 2,
      "title": "Corvana - Steady as she goes",
      "publisher": "Bank A Research",
      "published_at": "2024-05-14T00:00:00",
      "visibility": "external",
      "summary": "Research note reiterating a stable BB- view on the Republic of Corvana, reviewing its state-linked issuers, and recommending an overweight in the Corvana 2035s against Valdoria 2031s.",
      "topics": [
        "sovereign credit",
        "quasi-sovereigns",
        "rating view",
        "state ownership",
        "relative value"
      ],
      "about_on_path": [
        "INS-1010",
        "ISS-0001"
      ]
    },
    {
      "document_id": 6,
      "title": "UK Retail - Northbridge margins stabilise",
      "publisher": "Bank A Research",
      "published_at": "2026-07-01T00:00:00",
      "visibility": "external",
      "summary": "A research note reporting that Northbridge Retail's margins have stabilised and that the Market Weight recommendation on its 2029 bonds is unchanged.",
      "topics": [
        "retail",
        "margins",
        "market weight",
        "recommendation"
      ],
      "about_on_path": [
        "INS-1011"
      ]
    },
    {
      "document_id": 5,
      "title": "CNOC - Production steady, guarantee structure unchanged",
      "publisher": "Bank A Research",
      "published_at": "2026-06-10T00:00:00",
      "visibility": "external",
      "summary": "Research note saying CNOC's Q1 output was steady, that it remains state-owned, and that CNOC Finance B.V. still issues its USD debt with a parent guarantee, with the bonds trading wide of the sovereign curve.",
      "topics": [
        "guarantee",
        "ownership",
        "production",
        "spreads",
        "issuing entity"
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
      "summary": "Initiating coverage of Corvana Telecommunications (CorTel), a 35% state-owned company viewed as a standalone credit rated one notch above the sovereign with limited linkage to government finances.",
      "topics": [
        "initiating coverage",
        "telecommunications",
        "state ownership",
        "standalone credit",
        "sovereign linkage"
      ],
      "about_on_path": [
        "ISS-0001"
      ]
    }
  ],
  "notes": [
    "derivative sign convention is undocumented; quantities reported as in the OMS"
  ]
}
```

</details>

### 3. get_path(instrument_id='INS-1010', target_id='ISS-0001', channel_key='CORRELATED_WITH')

<details><summary>result</summary>

```json
{
  "key": "CORRELATED_WITH",
  "label": "correlation 0.7 with the sovereign",
  "grade": "low",
  "hops": [
    {
      "from_node": "instrument:INS-1010",
      "predicate": "ISSUED_BY",
      "to_node": "issuer:ISS-0009",
      "grade": "high",
      "citations": [
        {
          "statement_id": null,
          "edge_id": "instruments:INS-1010:issuer_id",
          "predicate": "ISSUED_BY",
          "source_system": "SecMaster",
          "source_file": "reference/instruments.csv",
          "document_title": null,
          "published_at": null,
          "as_of": "2026-10-27",
          "quote": "Republic of Valdoria",
          "status": "REFERENCE",
          "method": null,
          "visibility": null,
          "tier": 3
        }
      ]
    },
    {
      "from_node": "issuer:ISS-0009",
      "predicate": "CORRELATED_WITH",
      "to_node": "issuer:ISS-0001",
      "grade": "low",
      "citations": [
        {
          "statement_id": 20,
          "edge_id": "stmt:20",
          "predicate": "CORRELATED_WITH",
          "source_system": "ResearchHub",
          "source_file": "research/2025-11-18_bank-b_valdoria-spillovers.md",
          "document_title": "Valdoria - Neighbour risk overstated",
          "published_at": "2025-11-18T00:00:00",
          "as_of": "2025-11-18",
          "quote": "in risk-off episodes the correlation of 5Y CDS has been around 0.7",
          "status": "PROPOSED",
          "method": "MANUAL",
          "visibility": "external",
          "tier": 1
        }
      ]
    }
  ],
  "paths_considered": 1,
  "user": "alice",
  "as_of": "2026-10-27",
  "instrument_id": "INS-1010",
  "target_id": "ISS-0001"
}
```

</details>

### 4. get_document(document_id=7)

<details><summary>result</summary>

```json
{
  "document_id": 7,
  "source_system": "ResearchHub",
  "source_file": "research/2026-08-21_macro-internal_cvd-reserves.md",
  "kind": "RESEARCH",
  "title": "CVD - reserves under pressure",
  "publisher": "Internal - EM Macro",
  "author": "EM Macro team",
  "published_at": "2026-08-21T00:00:00",
  "visibility": "macro_internal",
  "about_issuers": [
    "ISS-0001"
  ],
  "about_instruments": [
    "INS-1004",
    "INS-2002",
    "INS-2003"
  ],
  "about_curves": [
    "CVD-GOVT"
  ],
  "about_currencies": [
    "CVD",
    "USD"
  ],
  "topics": [
    "fx reserves",
    "downgrade",
    "usd/cvd",
    "ndf",
    "rates hedge"
  ],
  "summary": "EM macro note arguing Corvana's falling FX reserves will pressure the dinar, favouring long USD/CVD via NDFs and paying CVD 5Y swaps to hedge a possible sovereign downgrade and local bond outflows.",
  "annotated_by": "LLM",
  "text": "\nFX reserves at the central bank of Corvana have fallen for five straight months and now cover 3.2 months of\nimports. We think pressure on the dinar builds into Q4. Our preferred expression is long USD/CVD via 3M NDFs.\n\nA rating downgrade of the ROC would likely trigger index-driven outflows from local bonds (CVGBs), pushing the\nCVD govt curve higher and steeper, with the 2033 most exposed. Paying CVD 5Y swaps is a cleaner hedge than\nshorting bonds given repo constraints.\n"
}
```

</details>

### 5. get_document(document_id=8)

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
  "summary": "Research note arguing that Agency A's negative outlook on the Republic of Corvana raises downgrade risk and assessing read-across to related issuers and Valdoria, recommending buying 5Y CDS protection.",
  "annotated_by": "LLM",
  "text": "\nFollowing Agency A's revision of the outlook to Negative on 18 September, we see a ~60% probability of a\none-notch downgrade to B+ within six months. Fiscal slippage from energy subsidies is the main driver.\n\nRead-across:\n- Corvana Oil (CNOC) - rating capped at the sovereign; USD bonds issued via its Dutch finance subsidiary carry\n  a full parent guarantee. Expect a one-for-one move.\n- CDB - explicitly guaranteed, will move with the sovereign.\n- First Corvana Bank - roughly 28% of assets in government securities; the sovereign-bank nexus means FCB is\n  exposed despite being privately owned.\n- Republic of Valdoria - limited direct trade linkage, but EM sovereign funds often hold both; some spillover\n  likely.\n\nWe recommend buying 5Y CDS protection on the sovereign.\n"
}
```

</details>

### 6. get_document(document_id=3)

<details><summary>result</summary>

```json
{
  "document_id": 3,
  "source_system": "ResearchHub",
  "source_file": "research/2025-11-18_bank-b_valdoria-spillovers.md",
  "kind": "RESEARCH",
  "title": "Valdoria - Neighbour risk overstated",
  "publisher": "Bank B Research",
  "author": "CEEMEA Credit Strategy",
  "published_at": "2025-11-18T00:00:00",
  "visibility": "external",
  "about_issuers": [
    "ISS-0001",
    "ISS-0009"
  ],
  "about_instruments": [],
  "about_curves": [],
  "about_currencies": [],
  "topics": [
    "proxy",
    "contagion",
    "correlation",
    "cds",
    "trade linkages"
  ],
  "summary": "A research note arguing that Valdoria's use as a trading proxy for Corvana overstates the neighbour risk, since bilateral trade is small even though 5Y CDS correlation rises in risk-off episodes.",
  "annotated_by": "LLM",
  "text": "\nInvestors often trade Valdoria as a proxy for Corvana. We think this is overstated: bilateral trade is under 4%\nof Valdoria GDP. That said, in risk-off episodes the correlation of 5Y CDS has been around 0.7.\n"
}
```

</details>

### 7. get_statements(entity_id='ISS-0009', predicate=None, as_of=None)

<details><summary>result</summary>

```json
{
  "entity_id": "ISS-0009",
  "predicate": null,
  "as_of": "2026-10-27",
  "current": [
    {
      "statement_id": null,
      "edge_id": "country:QV:sovereign_issuer_id",
      "subject_type": "country",
      "subject_id": "QV",
      "predicate": "SOVEREIGN_IS",
      "object_type": "issuer",
      "object_id": "ISS-0009",
      "value_num": null,
      "value_text": null,
      "holds": true,
      "as_of": "2026-10-27",
      "status": "REFERENCE",
      "method": null,
      "visibility": null,
      "tier": 3,
      "source_system": "Curated",
      "source_file": "curation/countries.yaml",
      "document_title": null,
      "published_at": null,
      "quote": "country.sovereign_issuer_id",
      "hidden_newer_count": 0
    },
    {
      "statement_id": null,
      "edge_id": "instruments:INS-1010:issuer_id",
      "subject_type": "instrument",
      "subject_id": "INS-1010",
      "predicate": "ISSUED_BY",
      "object_type": "issuer",
      "object_id": "ISS-0009",
      "value_num": null,
      "value_text": null,
      "holds": true,
      "as_of": "2026-10-27",
      "status": "REFERENCE",
      "method": null,
      "visibility": null,
      "tier": 3,
      "source_system": "SecMaster",
      "source_file": "reference/instruments.csv",
      "document_title": null,
      "published_at": null,
      "quote": "Republic of Valdoria",
      "hidden_newer_count": 0
    },
    {
      "statement_id": 20,
      "edge_id": "stmt:20",
      "subject_type": "issuer",
      "subject_id": "ISS-0009",
      "predicate": "CORRELATED_WITH",
      "object_type": "issuer",
      "object_id": "ISS-0001",
      "value_num": "0.7000",
      "value_text": "5Y CDS correlation in risk-off episodes",
      "holds": true,
      "as_of": "2025-11-18",
      "status": "PROPOSED",
      "method": "MANUAL",
      "visibility": "external",
      "tier": 1,
      "source_system": "ResearchHub",
      "source_file": "research/2025-11-18_bank-b_valdoria-spillovers.md",
      "document_title": "Valdoria - Neighbour risk overstated",
      "published_at": "2025-11-18T00:00:00",
      "quote": "in risk-off episodes the correlation of 5Y CDS has been around 0.7",
      "hidden_newer_count": 0
    },
    {
      "statement_id": 11,
      "edge_id": "stmt:11",
      "subject_type": "issuer",
      "subject_id": "ISS-0009",
      "predicate": "COUNTRY_OF_RISK",
      "object_type": "country",
      "object_id": "QV",
      "value_num": null,
      "value_text": null,
      "holds": true,
      "as_of": "2026-01-15",
      "status": "INFERRED",
      "method": "RULE",
      "visibility": null,
      "tier": 3,
      "source_system": "SecMaster",
      "source_file": "reference/issuers.csv",
      "document_title": null,
      "published_at": null,
      "quote": "rule: country of risk defaults to country of incorporation (issuers.country_of_incorporation = QV)",
      "hidden_newer_count": 0
    },
    {
      "statement_id": 19,
      "edge_id": "stmt:19",
      "subject_type": "issuer",
      "subject_id": "ISS-0009",
      "predicate": "TRADES_AS_PROXY_FOR",
      "object_type": "issuer",
      "object_id": "ISS-0001",
      "value_num": null,
      "value_text": "proxy trade overstated; bilateral trade under 4% of Valdoria GDP",
      "holds": false,
      "as_of": "2025-11-18",
      "status": "PROPOSED",
      "method": "MANUAL",
      "visibility": "external",
      "tier": 1,
      "source_system": "ResearchHub",
      "source_file": "research/2025-11-18_bank-b_valdoria-spillovers.md",
      "document_title": "Valdoria - Neighbour risk overstated",
      "published_at": "2025-11-18T00:00:00",
      "quote": "Investors often trade Valdoria as a proxy for Corvana. We think this is overstated",
      "hidden_newer_count": 0
    }
  ],
  "other_sources": [],
  "flags": [],
  "hidden_newer_count": 0
}
```

</details>

## Answer

**Five of your six EM_MACRO positions are tied to the Republic of Corvana: four directly and one possibly. The only one with no link is Northbridge Retail. Every holding was identified, so none is left unclassified.**

Corvana is rated BB- by Agency A. The outlook was cut from Stable to Negative on 2026-09-18.

## Exposed positions

| Position | Size | How it's linked |
|---|---|---|
| **Corvana Government Bond 10.5% 2033** (INS-1004) | CVD 450m | Three ways: Corvana issues it [instruments:INS-1004:issuer_id]; it's priced off the CVD-GOVT curve [instruments:INS-1004:underlying_curve, curves:CVD-GOVT:currency, country:QC:currency, country:QC:sovereign_issuer_id]; and it's in Corvana's currency, CVD [instruments:INS-1004:currency]. |
| **Republic of Corvana 6.5% 2030** (INS-1001) | USD 15m | Corvana issues it [instruments:INS-1001:issuer_id]. It's in USD, so there's no currency link. |
| **CVD 5Y pay-fixed swap** (INS-2003) | CVD 800m | It's priced off the CVD-OIS curve [instruments:INS-2003:underlying_curve, curves:CVD-OIS:currency, country:QC:currency, country:QC:sovereign_issuer_id] and is in CVD [instruments:INS-2003:currency]. |
| **USD/CVD 3M NDF** (INS-2002) | USD 25m | It's in CVD [instruments:INS-2002:currency, country:QC:currency, country:QC:sovereign_issuer_id]. |

All of these links are rated high-confidence. The tool doesn't record which way your derivatives face: swap and forward quantities are shown exactly as in your order system. So check the direction of the swap and NDF before deciding whether they gain or lose in a downgrade.

## Possibly exposed (unconfirmed)

- **Republic of Valdoria 8% 2031** (INS-1010), USD 8m. Valdoria issues it [instruments:INS-1010:issuer_id]. Its only link to Corvana is a 0.7 correlation in 5Y CDS during risk-off episodes [stmt 20]. That figure is research only, unconfirmed, and dates from 2025-11-18. The same note argues that trading Valdoria as a stand-in for Corvana is a mistake [stmt 19, also research only, unconfirmed].

## Not exposed

- **Northbridge Retail 4.25% 2029** (INS-1011), GBP 5m: no link found.

## What the research says

- **Internal EM Macro, 2026-08-21 (doc 7):** This note fits your book closely. It says a downgrade "would likely trigger index-driven outflows from local bonds (CVGBs), pushing the CVD govt curve higher and steeper, with the 2033 most exposed." That is your largest cash position. It prefers being "long USD/CVD via 3M NDFs" because "FX reserves... have fallen for five straight months and now cover 3.2 months of imports." It also argues that "Paying CVD 5Y swaps is a cleaner hedge than shorting bonds given repo constraints." Your NDF and pay-fixed swap match the trades it describes.
- **Bank B, 2026-09-22 (doc 8):** After the outlook cut, Bank B sees "a ~60% probability of a one-notch downgrade to B+ within six months," mainly because of "fiscal slippage from energy subsidies." On Valdoria it sees "limited direct trade linkage, but EM sovereign funds often hold both; some spillover likely." It recommends "buying 5Y CDS protection on the sovereign." It also discusses knock-on effects for other Corvana-linked issuers (CNOC, CDB, First Corvana Bank), but you don't hold any of them.
- **Bank B, 2025-11-18 (doc 3):** On Valdoria, the note argues the stand-in trade "is overstated: bilateral trade is under 4% of Valdoria GDP," but adds that "in risk-off episodes the correlation of 5Y CDS has been around 0.7."

Older research is also available but not quoted here: Bank A's stable-outlook note on Corvana from 2024-05 (doc 2), and Bank A notes on CNOC, CorTel and Northbridge.

**In short:** a downgrade would hit you directly through the two Corvana bonds, with the 2033 local bond most exposed. It would also move your CVD rates and FX trades through the curve and the currency; check their direction to see whether they offset the bond losses. Valdoria is a possible secondary effect, based on research only, unconfirmed.

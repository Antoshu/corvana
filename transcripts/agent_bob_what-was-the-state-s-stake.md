# Agent transcript: bob, as of 2026-10-27

Model: claude-opus-5-5

## Question

What was the state's stake in Corvana Power & Light on 2025-06-30, and what is it now?

## Tool calls

### 1. find_entity(query='Corvana Power & Light')

<details><summary>result</summary>

```json
[
  {
    "entity_type": "issuer",
    "entity_id": "ISS-0003",
    "name": "Corvana Power & Light plc",
    "matched_alias": "Corvana Power & Light",
    "match_kind": "alias"
  }
]
```

</details>

### 2. get_statements(entity_id='ISS-0003', predicate='OWNS', as_of='2025-06-30')

<details><summary>result</summary>

```json
{
  "entity_id": "ISS-0003",
  "predicate": "OWNS",
  "as_of": "2025-06-30",
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
    }
  ],
  "other_sources": [
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
    }
  ],
  "hidden_newer_count": 0
}
```

</details>

### 3. get_statements(entity_id='ISS-0003', predicate='OWNS', as_of=None)

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

## Answer

**On 2025-06-30, the Republic of Corvana held 51% of Corvana Power & Light plc (CPL). Today, the official record still shows 51%, but newer research says the stake was cut to 34% in February 2026. That 34% figure is research only and hasn't been confirmed.**

**On 2025-06-30: 51%**
- The ownership tracker records the state holding 51%, based on CPL's 2023 annual report and dated 2023-12-31: "Republic of Corvana (MinFin) -> Corvana Power & Light plc 51% (CPL annual report 2023)" [ownership:3].
- A May 2024 research note says the same: "Corvana Power & Light (51% state-owned) offers modest pick-up" [stmt 17]. It is research only, unconfirmed, but it agrees with the tracker.

**Today (2026-10-27): officially 51%, but the 51% figure is likely out of date**
- The ownership tracker is still the source that takes priority, and it still shows 51% as of 2023-12-31 [ownership:3].
- The system flags that 51% as stale. A credit-internal research note published 2026-03-05, with information dated 2026-02-24, says "The government sold down its stake from 51% to 34%" [stmt 21]. It also says this was "after partial IPO; golden share over tariff decisions retained" [stmt 21]. A golden share would let the state keep a say over tariff decisions.
- The same note says "a strategic investor now holds 25%" [stmt 22]. It doesn't name the investor. This is also research only, unconfirmed.

The likely current position is a 34% state stake, with the state keeping control over tariff decisions through the golden share. Until the tracker is updated to match the February 2026 change, the official figure stays at 51%. I could not identify the 25% investor.

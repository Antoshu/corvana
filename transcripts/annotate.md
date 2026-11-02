# Grounded LLM annotation (claude-sonnet-5-5), threshold 0.5, updated_on 2026-10-27

### document 1 `research/2023-10-02_bank-a_cortel-initiation.md`

- about_* ids: 1 (scan only 1, LLM only 0, both 1; both = unambiguous match the model confirmed, LLM only = its choice on an ambiguous span or an added mention): about_issuers ISS-0005
- topics: initiating coverage, state ownership, standalone credit, sovereign linkage
- summary (pointer, not a citation): Initiating coverage note on Corvana Telecommunications (CorTel), a 35% state-owned company viewed as a standalone credit rated one notch above the sovereign.
- mentions:
  - [1] "CorTel" -> ISS-0005 conf 0.98: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0005 (Corvana Telecommunications SA)
  - [2] "Corvana" -> null conf 0.95: kept (unambiguous scan match, always kept; the model said null (conf 0.95)); candidates: country QC (Corvana)
  - [3] "Corvana Telecommunications" -> ISS-0005 conf 0.98: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0005 (Corvana Telecommunications SA)
  - [4] "CorTel" -> ISS-0005 conf 0.98: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0005 (Corvana Telecommunications SA)

### document 2 `research/2024-05-14_bank-a_corvana-sovereign-outlook.md`

- about_* ids: 7 (scan only 1, LLM only 0, both 7; both = unambiguous match the model confirmed, LLM only = its choice on an ambiguous span or an added mention): about_issuers ISS-0001, ISS-0002, ISS-0003, ISS-0004; about_instruments INS-1002, INS-1010; about_currencies USD
- topics: sovereign credit, quasi-sovereigns, state ownership, guarantee, relative value
- summary (pointer, not a citation): A research note reiterating a stable BB- view on the Republic of Corvana, reviewing its state-linked issuers, and recommending an overweight in the Corvana 2035s against Valdoria 2031s.
- mentions:
  - [1] "Corvana" -> ISS-0001 conf 0.60: kept (model's choice among the candidates); candidates: country QC (Corvana); issuer ISS-0001 (Republic of Corvana)
  - [2] "Republic of Corvana" -> ISS-0001 conf 0.98: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0001 (Republic of Corvana)
  - [3] "Corvana" -> null conf 0.90: kept (unambiguous scan match, always kept; the model said null (conf 0.90)); candidates: country QC (Corvana)
  - [4] "CNOC" -> ISS-0002 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0002 (Corvana National Oil Company)
  - [5] "CNOC" -> ISS-0002 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0002 (Corvana National Oil Company)
  - [6] "USD" -> USD conf 0.98: kept (unambiguous scan match, confirmed by the model); candidates: currency USD (USD)
  - [7] "Corvana" -> null conf 0.92: kept (unambiguous scan match, always kept; the model said null (conf 0.92)); candidates: country QC (Corvana)
  - [8] "Corvana Power & Light" -> ISS-0003 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0003 (Corvana Power & Light plc)
  - [9] "Corvana" -> null conf 0.92: kept (unambiguous scan match, always kept; the model said null (conf 0.92)); candidates: country QC (Corvana)
  - [10] "Corvana Development Bank" -> ISS-0004 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0004 (Corvana Development Bank)
  - [11] "CORVAN" -> null conf 0.85: kept (unambiguous scan match, always kept; the model said null (conf 0.85)); candidates: issuer ISS-0001 (Republic of Corvana)
  - [12] "CORVAN 2035s" -> INS-1002 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: instrument INS-1002 (Republic of Corvana 7.25% 2035)
  - [13] "Valdoria" -> null conf 0.85: DROPPED (model: not a reference to any candidate); candidates: country QV (Valdoria); issuer ISS-0009 (Republic of Valdoria)
  - [14] "Valdoria 2031s" -> INS-1010 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: instrument INS-1010 (Republic of Valdoria 8% 2031)

### document 3 `research/2025-11-18_bank-b_valdoria-spillovers.md`

- about_* ids: 2 (scan only 0, LLM only 3, both 0; both = unambiguous match the model confirmed, LLM only = its choice on an ambiguous span or an added mention): about_issuers ISS-0001, ISS-0009
- topics: proxy, contagion, correlation, cds, neighbour risk
- summary (pointer, not a citation): A research note arguing that Valdoria's role as a trading proxy for Corvana is overstated given limited bilateral trade, though 5Y CDS correlation rises in risk-off episodes.
- mentions:
  - [1] "Valdoria" -> ISS-0009 conf 0.60: kept (model's choice among the candidates); candidates: country QV (Valdoria); issuer ISS-0009 (Republic of Valdoria)
  - [2] "Valdoria" -> ISS-0009 conf 0.60: kept (model's choice among the candidates); candidates: country QV (Valdoria); issuer ISS-0009 (Republic of Valdoria)
  - [3] "Corvana" -> ISS-0001 conf 0.60: kept (model's choice among the candidates); candidates: country QC (Corvana); issuer ISS-0001 (Republic of Corvana)
  - [4] "Valdoria" -> QV conf 0.75: kept (model's choice among the candidates); candidates: country QV (Valdoria); issuer ISS-0009 (Republic of Valdoria)

### document 4 `research/2026-03-05_em-credit-internal_cpl-ipo.md`

- about_* ids: 1 (scan only 1, LLM only 0, both 1; both = unambiguous match the model confirmed, LLM only = its choice on an ambiguous span or an added mention): about_issuers ISS-0003
- topics: ipo, sovereign linkage, beta, golden share, downgrade
- summary (pointer, not a citation): Research note arguing that after its partial IPO, Corvana Power & Light should trade with a lower beta to the sovereign, while remaining exposed to a sovereign downgrade through tariffs and state receivables.
- mentions:
  - [1] "CPL" -> ISS-0003 conf 0.98: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0003 (Corvana Power & Light plc)
  - [2] "Corvana" -> null conf 0.93: kept (unambiguous scan match, always kept; the model said null (conf 0.93)); candidates: country QC (Corvana)
  - [3] "Corvana Power & Light" -> ISS-0003 conf 0.98: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0003 (Corvana Power & Light plc)
  - [4] "CPL" -> ISS-0003 conf 0.98: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0003 (Corvana Power & Light plc)
  - [5] "CPL" -> ISS-0003 conf 0.98: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0003 (Corvana Power & Light plc)

### document 5 `research/2026-06-10_bank-a_cnoc-update.md`

- about_* ids: 4 (scan only 1, LLM only 0, both 4; both = unambiguous match the model confirmed, LLM only = its choice on an ambiguous span or an added mention): about_issuers ISS-0001, ISS-0002, ISS-0007; about_currencies USD
- topics: guarantee, production, ownership, spreads, sovereign curve
- summary (pointer, not a citation): Research note on Corvana National Oil Company (CNOC) saying Q1 output was steady, the state ownership and CNOC Finance B.V. guarantee structure for USD debt are unchanged, and its bonds trade 20-30bp wide of the sovereign curve.
- mentions:
  - [1] "CNOC" -> ISS-0002 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0002 (Corvana National Oil Company)
  - [2] "Corvana" -> null conf 0.95: kept (unambiguous scan match, always kept; the model said null (conf 0.95)); candidates: country QC (Corvana)
  - [3] "Corvana Oil" -> ISS-0002 conf 0.98: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0002 (Corvana National Oil Company)
  - [4] "Ministry of Finance" -> ISS-0001 conf 0.95: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0001 (Republic of Corvana)
  - [5] "CNOC Finance B.V." -> ISS-0007 conf 0.99: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0007 (CNOC Finance B.V.)
  - [6] "USD" -> USD conf 0.99: kept (unambiguous scan match, confirmed by the model); candidates: currency USD (USD)
  - [7] "CNOC" -> ISS-0002 conf 0.60: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0002 (Corvana National Oil Company)

### document 6 `research/2026-07-01_bank-a_uk-retail.md`

- about_* ids: 2 (scan only 0, LLM only 0, both 2; both = unambiguous match the model confirmed, LLM only = its choice on an ambiguous span or an added mention): about_issuers ISS-0010; about_instruments INS-1011
- topics: retail, margins, market weight, recommendation
- summary (pointer, not a citation): A research note on UK retailer Northbridge Retail reporting stable margins and keeping a Market Weight recommendation on its 2029 bonds.
- mentions:
  - [1] "Northbridge" -> ISS-0010 conf 0.90: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0010 (Northbridge Retail Group plc)
  - [2] "Northbridge Retail" -> ISS-0010 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0010 (Northbridge Retail Group plc)
  - [3] "NBRTL" -> null conf 0.85: kept (unambiguous scan match, always kept; the model said null (conf 0.85)); candidates: issuer ISS-0010 (Northbridge Retail Group plc)
  - [4] "NBRTL 2029s" -> INS-1011 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: instrument INS-1011 (Northbridge Retail 4.25% 2029)
- added by the model:
  - GB "UK" conf 0.60: DROPPED (country has no about_* column (reported only))

### document 7 `research/2026-08-21_macro-internal_cvd-reserves.md`

- about_* ids: 7 (scan only 0, LLM only 2, both 6; both = unambiguous match the model confirmed, LLM only = its choice on an ambiguous span or an added mention): about_issuers ISS-0001; about_instruments INS-1004, INS-2002, INS-2003; about_curves CVD-GOVT; about_currencies CVD, USD
- topics: fx reserves, downgrade, usd/cvd ndf, rates hedge, local bonds
- summary (pointer, not a citation): Internal EM macro note arguing that falling Corvana FX reserves will pressure the dinar and recommending long USD/CVD via NDFs and paying CVD 5Y swaps as a hedge against a possible downgrade of the Republic of Corvana.
- mentions:
  - [1] "CVD" -> CVD conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: currency CVD (CVD)
  - [2] "Corvana" -> QC conf 0.85: kept (model's choice among the candidates); candidates: country QC (Corvana); issuer ISS-0001 (Republic of Corvana)
  - [3] "USD" -> USD conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: currency USD (USD)
  - [4] "CVD" -> CVD conf 0.95: kept (unambiguous scan match, confirmed by the model); candidates: currency CVD (CVD)
  - [5] "3M NDFs" -> INS-2002 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: instrument INS-2002 (USD/CVD 3M non-deliverable forward)
  - [6] "ROC" -> ISS-0001 conf 0.98: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0001 (Republic of Corvana)
  - [7] "CVD" -> null conf 0.85: kept (unambiguous scan match, always kept; the model said null (conf 0.85)); candidates: currency CVD (CVD)
  - [8] "CVD govt curve" -> CVD-GOVT conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: curve CVD-GOVT (Corvana local-currency government bond curve)
  - [9] "CVD" -> null conf 0.85: kept (unambiguous scan match, always kept; the model said null (conf 0.85)); candidates: currency CVD (CVD)
  - [10] "CVD 5Y swaps" -> INS-2003 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: instrument INS-2003 (CVD 5Y pay-fixed interest rate swap)
- added by the model:
  - INS-1004 "the 2033" conf 0.80: kept (known id, verbatim text)

### document 8 `research/2026-09-22_bank-b_corvana-negative-watch.md`

- about_* ids: 8 (scan only 2, LLM only 2, both 7; both = unambiguous match the model confirmed, LLM only = its choice on an ambiguous span or an added mention): about_issuers ISS-0001, ISS-0002, ISS-0004, ISS-0006, ISS-0007, ISS-0009; about_instruments INS-2001; about_currencies USD
- topics: outlook negative, downgrade risk, sovereign-bank nexus, guarantee, cds
- summary (pointer, not a citation): Bank B Research says Agency A's negative outlook on the Republic of Corvana raises downgrade risk, discusses read-across to CNOC, CDB, First Corvana Bank and Valdoria, and recommends buying 5Y CDS protection on the sovereign.
- mentions:
  - [1] "Republic of Corvana" -> ISS-0001 conf 0.98: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0001 (Republic of Corvana)
  - [2] "Corvana" -> null conf 0.90: kept (unambiguous scan match, always kept; the model said null (conf 0.90)); candidates: country QC (Corvana)
  - [3] "Corvana" -> null conf 0.95: kept (unambiguous scan match, always kept; the model said null (conf 0.95)); candidates: country QC (Corvana)
  - [4] "Corvana Oil" -> ISS-0002 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0002 (Corvana National Oil Company)
  - [5] "CNOC" -> ISS-0002 conf 0.95: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0002 (Corvana National Oil Company)
  - [6] "USD" -> USD conf 0.95: kept (unambiguous scan match, confirmed by the model); candidates: currency USD (USD)
  - [7] "Dutch" -> NL conf 0.90: kept (unambiguous scan match, confirmed by the model); candidates: country NL (Netherlands)
  - [8] "CDB" -> ISS-0004 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0004 (Corvana Development Bank)
  - [9] "First Corvana Bank" -> ISS-0006 conf 0.98: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0006 (First Corvana Bank)
  - [10] "Corvana" -> null conf 0.95: kept (unambiguous scan match, always kept; the model said null (conf 0.95)); candidates: country QC (Corvana)
  - [11] "FCB" -> ISS-0006 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0006 (First Corvana Bank)
  - [12] "Republic of Valdoria" -> ISS-0009 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0009 (Republic of Valdoria)
  - [13] "Valdoria" -> null conf 0.93: kept (unambiguous scan match, always kept; the model said null (conf 0.93)); candidates: country QV (Valdoria)
- added by the model:
  - INS-2001 "5Y CDS protection" conf 0.60: kept (known id, verbatim text)
  - ISS-0007 "its Dutch finance subsidiary" conf 0.60: kept (known id, verbatim text)

### document 9 `desk_notes/em-credit-desk-notes.md`

- about_* ids: 2 (scan only 0, LLM only 0, both 2; both = unambiguous match the model confirmed, LLM only = its choice on an ambiguous span or an added mention): about_issuers ISS-0001, ISS-0005
- topics: sovereign proxy, ownership, spreads, government stake
- summary (pointer, not a citation): A desk note reminding that CorTel trades as a sovereign proxy, moving with Corvana sovereign spreads despite the government's reduced 20% stake after the 2025 placement.
- mentions:
  - [1] "CorTel" -> ISS-0005 conf 0.98: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0005 (Corvana Telecommunications SA)
  - [2] "CORVAN" -> ISS-0001 conf 0.90: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0001 (Republic of Corvana)

### document 10 `desk_notes/em-credit-desk-notes.md`

- about_* ids: 1 (scan only 0, LLM only 1, both 1; both = unambiguous match the model confirmed, LLM only = its choice on an ambiguous span or an added mention): about_issuers ISS-0008
- topics: country of risk, meridian mining, data correction, domicile
- summary (pointer, not a citation): A desk note saying Meridian Mining's country of risk should be Corvana because all its mines are there, even though it is UK listed and incorporated and the risk system still shows GB.
- mentions:
  - [1] "Meridian" -> ISS-0008 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0008 (Meridian Mining plc)
  - [2] "Corvana" -> QC conf 0.95: kept (model's choice among the candidates); candidates: country QC (Corvana); issuer ISS-0001 (Republic of Corvana)
  - [3] "Corvana" -> QC conf 0.97: kept (model's choice among the candidates); candidates: country QC (Corvana); issuer ISS-0001 (Republic of Corvana)
- added by the model:
  - GB "GB" conf 0.90: DROPPED (country has no about_* column (reported only))
  - GB "UK" conf 0.90: DROPPED (country has no about_* column (reported only))

### document 11 `desk_notes/em-credit-desk-notes.md`

- about_* ids: 3 (scan only 1, LLM only 0, both 2; both = unambiguous match the model confirmed, LLM only = its choice on an ambiguous span or an added mention): about_issuers ISS-0003, ISS-0004; about_instruments INS-1007
- topics: guarantee, outlook change, sovereign linkage, ipo
- summary (pointer, not a citation): A desk chat note reminding that the Corvana Development Bank 2027 bonds are guaranteed and so trade like sovereign debt, while Corvana Power & Light is less so after its IPO.
- mentions:
  - [1] "CDB" -> null conf 0.90: kept (unambiguous scan match, always kept; the model said null (conf 0.90)); candidates: issuer ISS-0004 (Corvana Development Bank)
  - [2] "CDB 27s" -> INS-1007 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: instrument INS-1007 (Corvana Development Bank 4.75% 2027)
  - [3] "CPL" -> ISS-0003 conf 0.95: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0003 (Corvana Power & Light plc)

### document 12 `desk_notes/em-credit-desk-notes.md`

- about_* ids: 1 (scan only 0, LLM only 0, both 1; both = unambiguous match the model confirmed, LLM only = its choice on an ambiguous span or an added mention): about_issuers ISS-0006
- topics: bank exposure, sovereign risk, sovereign-bank nexus
- summary (pointer, not a citation): A desk-chat line noting that FCB is not held in the book but is the bank most exposed to the sovereign.
- mentions:
  - [1] "FCB" -> ISS-0006 conf 0.97: kept (unambiguous scan match, confirmed by the model); candidates: issuer ISS-0006 (First Corvana Bank)

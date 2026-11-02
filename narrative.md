# Corvana knowledge layer – narrative

This is the Part 4 write-up. Sections 1 to 5 answer the five questions in the brief. Section 6 is how I got
there: the decisions I made along the way, where I disagreed with the AI tooling and why, written as a log so the
reasoning can be followed. `README.md` has the run commands; `model/` has the ground truth, the table-by-table
review and the schema; `ai_tooling_notes.md` is the note on how the AI tooling was used.

The scenario: *"If the Republic of Corvana is downgraded, what in my book is exposed, how, and what does our
research say about it?"* Everything below was derived from that one question, asked by alice and by bob.

## 1. The model

**Scope decision.** Only the tables and properties necessary to answer the question (as I understand it) have been
modelled. While there are multiple ways to "design a knowledge model" as requested in the brief (YAML, Turtle,
etc.), I decided to model the data and relationships with bullet point 2 in mind. Since the request is to load the
data into the model, I interpreted the "model" as possibly just being a database schema with tables and references
in one DBML file. I like DBML because it can generate SQL natively, is quite expressive while staying easy for a
human to read, and has visual support (https://dbdiagram.io/).

Model content:

1. **Source tables, as delivered.** I created one table per file, plus tables for entities (like country) that can be
   expected to have their own properties in the context of the data. Tables: `issuers`, `instruments`, `curves`,
   `ownership`, `ratings`, `positions`, plus `country` (code, currency, sovereign) and `rating_scale`. Columns not
   relevant to the question, to my understanding, were dropped (sector, issuer type, LEI, coupon, maturity). To
   these high-quality tables only two kinds of field were added: curated `aliases[]` on each entity table, and ids
   resolved from free-text names (`instruments.issuer_id` from "Corvana Ministry of Finance", `ownership.owner_id`,
   `ratings.issuer_id`). The raw name stays next to the id as evidence. Aliases are used throughout, either for id
   resolution or in the ETL process that turns documents (research, notes) into structured data. Aliases are key for
   entity resolution and should probably see human review during ingestion at some point.
2. **Statements.** One row per link per source, for the links no file column holds: either a rule (every issuer's
   country of risk from its incorporation; the CDB guarantee and the CNOC Finance vehicle read from the tracker's
   notes) or a document (stakes, guarantees, proxies, betas, correlations, a disputed country of risk). Each row
   carries subject, predicate, object, value, `as_of` (when it was true, not when it was published), source system,
   document, verbatim quote, method, status and visibility. Fourteen predicates are declared in `predicate_def`
   with how they compare and how a path walks them. Links a file column does hold (issuer, guarantor, owner,
   currency, curve, country → sovereign) are not copied: the `edges` view projects them next to the statements so
   path finding walks one graph.
3. **Documents.** One table for research notes and desk-chat lines: text, visibility label, and what each document
   is about as id arrays (`about_issuers`, `about_instruments`, ...), plus topics and a one-line summary. "Research
   about CPL" is a single lookup. I considered one table for notes and one for research, to avoid mixing sources,
   and merged them because the content is similar (unstructured opinion and information from individuals) and it
   simplifies the database; `source_system` keeps the two distinguishable, so splitting later is a partition, not
   a redesign.

**Metadata:** `sources` (the owner's own reliability word, mapped to a tier of 3/2/1) and `entitlements` (the YAML,
from which the Postgres roles are generated). In the DBML these sit in their own group so data and metadata are
visibly apart.

**Precedence and quality are views, never edits.** `current_statements(as_of)` ranks the rows on each link: a
person's confirmation first, then a file value or a rule, then research; within a rank the more reliable source,
then the newer date. The losers stay attached as other sources. `link_quality` names each disagreement:
CORROBORATED, STALE, CONFLICT, SUPERSEDED. `data_quality` adds unresolved position refs (with a nearest-match hint
that is never applied), unresolved names and RATING_LAG. Nothing is ever overwritten, so a point-in-time answer is
the same function with a different date.

**Left out, deliberately.** Prices and sizing (the question asks for the channel, not the size). Opinions in the 
notes are not transformed into any kind of structured data and are left as is to be quoted by the agent if need be.
Also left out: First Corvana Bank's exposure (no position reaches the sovereign through it). The
Ministry of Finance as a separate entity (an alias of the Republic). The unnamed CorTel holding company and the
CPL strategic investor (kept as unresolved subjects). 

**Why Postgres.** I picked Postgres because it is simple to implement for a proof of concept like this one while
still having all the required features:

1. It has row-level security, so I can enforce visibility at the database level. The advantage of not having this
   security in the MCP is primarily that we can offer users an SQL interface if they do not use agents, so the data
   interface is more versatile. Admins keep a bypass path (a superuser or a `BYPASSRLS` role sees everything).
2. At this scale it is lightweight, easy to set up and easy to understand and debug.
3. The data at this scale quite easily lends itself to a relational structure.

When moving to production, it is very likely that Postgres will not scale well. A real knowledge graph like Neo4j
will do much better because:

1. Data onboarding will be easier, since we can attach the same class and properties to different tables (say
   `issuers_internal` and `issuers_external`) without impacting traversal, whereas adding a new table to Postgres
   means changing joins.
2. Traversal over complex datasets will be much more understandable and efficient with Cypher queries, which deal
   with concepts rather than concrete table and column names.
3. Some of the data lends itself more to a quads format (for sourcing) than to a relational database, in my opinion,
   as there are many disparate data points coming from the research that are difficult to represent relationally
   without creating many more tables and columns.

The statements table is already an edge list with provenance, which is the migration path to a graph store when the
walk outgrows SQL (section 5). Two more choices worth stating: the table DDL is generated from the DBML and never
written by hand (a test fails if the two drift), while views, functions and security are hand-written SQL; and all
the logic stays in the database for now, because we are building with multiple vending methods in mind (agent, MCP,
direct SQL) and that keeps one definition for all of them, at the cost of big CTE queries being harder to read.

In an ideal world the database would have "time travel" so we could inspect the state at any past moment when something goes wrong.
Right now the solution with Postgres might be to create tables of values in time (pk + date) but using a data platform that natively
supports time travel would be better.

## 2. Identities, conflicts and stale data

**Resolving identities.** I've kept as much entity data as possible that could help for entity resolution/conflation. Data like tickers 
is very useful either to confirm the identity of an entity or to cross reference between datasets. For further resolution
across datasets where there might not be any proper ids to work with, say `ownership.owner`, I've created curated aliases 
for the entities such as "Rep. of Corvana", "Corvana Ministry of Finance", "CDB 27s", "3M NDFs"). An `alias` view
unions them and the entities are resolved at ingestion. Adding aliases over time allows for better resolution with validation rules
in the ingestion tools making sure rows indeed resolve to real ids (when necessary).
When matching on exact ids, the system does exact matches but raises flags for data quality in case of close matches. For
example, in positions, `XS2812345672` matches nothing and is reported as unresolved with "nearest known
ISIN XS2812345671; not applied". 

In documents, we do a grounded resolution of the entities by letting an LLM model retrieve entity names and attributes to find
which entity is the subject of the unstructured data. The model is also prompted to produce a confidence value between 0 and 1
that can be later used to refine what resolved values can directly be added to the DBs and which ones might require human review.

**Handling conflicts / stale data** I've made the explicit decision to keep conflicting data (in different tables) with the assumption that the 
conflict would primarily be between the high quality but potentially incomplete/outdated data from providers and the research/notes.
At a small data scale, this is ok because we can feed the agent both and let it present the uncertainty to the PM. The agent can then point out 
which data is unconfirmed or seems to be contradicted by newer data. The compromise here is getting a more complete and honest view of data 
for the price of making the output more complex.
In the current data model, there is a flag that could be manually changed to indicate a fact is unproven or has been verified to be true.

Ideally what we would get here is a single source of truth which would be the data from the providers, with potential overwrites 
(probably via joins) with human-in-the-loop verified data when we get newer notes/research contradicting the facts in the main tables.

## 3. Determinism vs LLM

I've chosen to have as much determinism as possible and only deferring to an LLM when absolutely necessary. For example, alias matches during
ingestion to enrich the data with ids (ownership.owner) is done deterministically which allows us to cheaply guarantee high quality matches assuming
some standard of data quality from the providers and manual verification of the aliases at some point.

I've used LLMs where they excel, retrieving structure out of large amounts of unstructured contents. For research and notes, I've therefore used
LLM tooling (model + grounding from the DB) to infer what entities are the subject of a particular document. This then allows us to tag and retrieve 
documents when they are relevant. At the moment, what I have built only creates a list of entities and does not yet retrieve extra facts and properties
but this probably should be done long term. Moreover, as the dataset of documents and notes increases, it will become impossible/impractical to just return the raw 
text from those documents, even if they are filtered beforehand. We should then use the LLM extracted facts as a backfill for the main database to avoid having
multiple sources of truth.
Right now, everything that comes from a document is flagged PROPOSED, so the final answer takes the lower trust into account instead of relying 
on it without telling the user.

## 4. Measuring accuracy and usefulness

**Check the quality of the system.** For that we need to test four things:
1. Raw data retrieval success. This can be tested with standard tests expecting a particular value (say checking if we indeed get the latest data)
2. Data quality. This needs to be tested using hard validation rules, as well as checking on inconsistencies with logic that the DB should follow if it is in a healthy state.
3. AI answer improvement. This can be tested using an LLM-as-a-judge by posing the same question with an without grounding and verifying all the facts given by the agent
against an expected set of facts to return
4. Agent quality. This again can be tested with an LLM-as-a-judge to check if it consistently returns the right data in the expected format given the same input

**Test questions with expected answers, runnable.** Each question stands on its own; the expected answer was written
by hand from the data before the code existed (`tests/expected/*.md`); the command runs the tests that assert it
against the live database. The whole set is `uv run pytest -q` (88 tests). Any question can also be put to the agent
as written: `uv run kl-agent --user <user> --question "..."`.

| # | question | expected answer | run |
|---|---|---|---|
| 1 | bob, as of 2026-10-27: "If the Republic of Corvana is downgraded, what in my book is exposed, how, and what does our research say about it?" | Exposed: CNOC Finance 2029 (guaranteed by CNOC, 100% state-owned), CDB 2027 (sovereign guarantee, corroborated by three documents), CPL 2031 (51% stake flagged stale, 34% research only), CorTel 2032 (20% stake and proxy, research only), the 5Y CDS (references the sovereign; sign undocumented). Meridian 2030 unconfirmed (desk view only, conflict with the GB default). XS2812345672 and XS2999887768 unresolved, never guessed. Research: Bank A 2024 and 2026, Bank B 2026-09-22, the CPL IPO note, the desk lines; never the macro note | `uv run pytest tests/test_questions.py -k bob_` |
| 2 | alice, as of 2026-10-27: same question | Exposed: CORVAN 6.5% 2030 and CVGB 10.5% 2033 (issued by the Republic; the CVGB link is inferred through "Corvana Ministry of Finance"), the CVD 5Y swap and the USD/CVD NDF (currency and curve). Valdoria 2031 research only (CDS correlation 0.7). Northbridge 2029 not exposed. Research: the macro note, Bank A 2024, Bank B; never the CPL IPO note or a desk line | `uv run pytest tests/test_questions.py -k alice_` |
| 3 | "What was the state's stake in Corvana Power & Light on 2025-06-30, and what is it now?" | On 2025-06-30: 51% for every user (tracker, corroborated by Bank A 2024). Now: bob and carol get 51% flagged stale with 34% (credit-internal, 2026-02-24) beside it; alice gets 51% and "newer information on this link exists that you are not entitled to see", one row, no content | `uv run pytest tests/test_questions.py -k cpl_stake` |
| 4 | alice: "What does our research say about Corvana Power & Light?" and bob: "What does our research say about the CVGB 2033 and the CVD curve?" | alice: Bank A 2024 (51% state-owned, modest pick-up) and nothing else; the CPL IPO note and its 34% never appear. bob: nothing; the macro note is the only research on the CVD curve and he is not entitled to it. Each user is told only what they may read, with no hint of the document itself | `uv run pytest tests/test_questions.py -k "documents or research_visible"` |
| 5 | bob, as of 2026-10-28: "Corvana was downgraded to B+ yesterday. What in my book is exposed, how, and what does our research say about it?" | The cut is dated 2026-10-28 (today, not yesterday). The new CNOC Finance 2034 bond (XS2999887768, unresolved the day before) is now exposed through the same channels as the 2029; Corvana and CNOC at B+; CDB still BB- and flagged as lagging its guarantor, which Bank B's new note calls inconsistent given the explicit guarantee; XS2812345672 still unresolved with "nearest known ISIN XS2812345671; not applied". Asked as of 2026-10-27 the answer is unchanged | `uv run pytest tests/test_update.py` (after `uv run kl-update data/updates/2026-10-28`) |
| 6 | bob: "Is Meridian Mining exposed to a Corvana downgrade?" | Unconfirmed: the risk system's default is GB (country of incorporation), the desk says Corvana ("every mine is in Corvana"), the two conflict and the agent says so. If the desk view is confirmed by a person, the answer becomes yes: Corvana is the current country of risk, the GB default is shown as superseded, and the holding is exposed on a confirmed channel | `uv run pytest tests/test_summary.py::test_confirmed_desk_row_overrides_inferred_reference` |


## 5. Next two weeks, and the whole firm

For the next two weeks: I think the priority is structured data extraction from the notes/research to maximise the data quality
and quantity. That would mean going beyond just identifying entities in those documents and making full triple style statements out of
everything in there. I would also like to not have independent "documents" tables that hold unstructured data but rather extract the data and
turn it into fully structured so that we can efficiently reference facts that originally came from these documents.
Then the priority would be to make a decision regarding the future of the data layer assuming a much broader dataset and deeper tables which is 
inevitable at the scale of the whole firm. Right now there are a few primary risks that will become apparent with data being ingested at scale: 1) context bloating
2) traversal speed decreasing 3) database complexity (difficulty to understand) 4) data auditing/maintenance becoming unmanageable

In my opinion, the best solution solution at that scale is probably to migrate to a proper knowledge graph with a single (if possible) ontology
across the entire firm so that everyone can understand what the data represents and query it efficiently. Depending on the data, we could imagine a
hybrid model where relationships between entities (ownership etc...) are stored in a graph while some other datapoints (for example live financial data)
is stored in an SQL database which will handle live writing of data better than a graph.

Finally, some basic infrastructure will have to be changed at the scale of the company, such as migrating to the cloud (or company servers)
and migrating the ingesting system to a proper ETL/ELT pipeline infrastructure.

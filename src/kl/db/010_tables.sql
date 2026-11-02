-- generated from model/schema.dbml by kl-schema; do not edit

CREATE TYPE "ref_type" AS ENUM (
  'ISIN',
  'INTERNAL',
  'TICKER'
);

CREATE TYPE "doc_kind" AS ENUM (
  'RESEARCH',
  'DESK_NOTE'
);

CREATE TYPE "annotator" AS ENUM (
  'RULE',
  'LLM'
);

CREATE TYPE "compare" AS ENUM (
  'object',
  'value_num',
  'holds'
);

CREATE TYPE "direction" AS ENUM (
  'forward',
  'backward'
);

CREATE TYPE "method" AS ENUM (
  'RULE',
  'MANUAL',
  'LLM'
);

CREATE TYPE "status" AS ENUM (
  'REFERENCE',
  'INFERRED',
  'PROPOSED',
  'CONFIRMED',
  'REJECTED'
);

-- ------------------------------------------------------------------------------------------------------------
-- Level 1 · source tables
-- ------------------------------------------------------------------------------------------------------------

CREATE TABLE "sources" (
  "source_id" text PRIMARY KEY,
  "description" text,
  "reliability" text,
  "source_file" text NOT NULL,
  "updated_on" date NOT NULL
);

COMMENT ON TABLE "sources" IS 'sources.yaml. Tier drives precedence between statements on the same link.';

COMMENT ON COLUMN "sources"."source_id" IS 'SecMaster, OMS, RatingsFeed, MarketData, OwnershipTracker, ResearchHub, DeskNotes, Curated';

COMMENT ON COLUMN "sources"."reliability" IS 'the words of the data owner; source_tier maps high→3, medium→2, else→1';

CREATE TABLE "entitlements" (
  "username" text PRIMARY KEY,
  "books" text[] NOT NULL,
  "research_visibility" text[] NOT NULL,
  "source_file" text NOT NULL,
  "updated_on" date NOT NULL
);

COMMENT ON TABLE "entitlements" IS 'entitlements.yaml. The loader creates one role per user, book_<book> and vis_<label> group roles from it.';

COMMENT ON COLUMN "entitlements"."research_visibility" IS 'labels: external, macro_internal, credit_internal';

CREATE TABLE "country" (
  "code" char(2) PRIMARY KEY,
  "name" text NOT NULL,
  "aliases" text[] NOT NULL DEFAULT '{}',
  "currency" char(3),
  "sovereign_issuer_id" text UNIQUE,
  "updated_on" date NOT NULL
);

COMMENT ON TABLE "country" IS 'Curated (curation/countries.yaml). QC → CVD → ISS-0001 is the end of every currency and curve channel.';

COMMENT ON COLUMN "country"."aliases" IS 'curated other names ("Corvanan")';

COMMENT ON COLUMN "country"."currency" IS 'CURRENCY_OF hop: currency → country';

COMMENT ON COLUMN "country"."sovereign_issuer_id" IS 'SOVEREIGN_IS hop: country → sovereign';

CREATE TABLE "rating_scale" (
  "agency" text NOT NULL,
  "rating" text NOT NULL,
  "rank" smallint NOT NULL,
  "updated_on" date NOT NULL,
  PRIMARY KEY ("agency", "rating")
);

CREATE UNIQUE INDEX ON "rating_scale" ("agency", "rank");

COMMENT ON TABLE "rating_scale" IS 'Curated. Only for rank comparison (RATING_LAG, "one notch above").';

COMMENT ON COLUMN "rating_scale"."rank" IS '1 = AAA … 22 = D';

CREATE TABLE "issuers" (
  "issuer_id" text PRIMARY KEY,
  "legal_name" text UNIQUE NOT NULL,
  "short_name" text,
  "aliases" text[] NOT NULL DEFAULT '{}',
  "country_of_incorporation" char(2) NOT NULL,
  "last_updated" date,
  "source_system" text NOT NULL,
  "source_file" text NOT NULL,
  "updated_on" date NOT NULL
);

COMMENT ON TABLE "issuers" IS 'issuers.csv minus lei, issuer_type, sector (on no path, in no citation), plus the curated aliases column. The names in the row (legal_name, short_name, aliases) are what the alias view resolves against.';

COMMENT ON COLUMN "issuers"."short_name" IS 'second file-supplied alias';

COMMENT ON COLUMN "issuers"."aliases" IS 'curated other names seen in the pack ("Rep. of Corvana", "Corvana Ministry of Finance"); GIN index';

COMMENT ON COLUMN "issuers"."country_of_incorporation" IS 'COUNTRY_OF_RISK rule input';

COMMENT ON COLUMN "issuers"."last_updated" IS 'as_of of rows inferred from this row';

CREATE TABLE "curves" (
  "curve_id" text PRIMARY KEY,
  "description" text,
  "aliases" text[] NOT NULL DEFAULT '{}',
  "currency" char(3) NOT NULL,
  "source_system" text NOT NULL,
  "source_file" text NOT NULL,
  "updated_on" date NOT NULL
);

COMMENT ON TABLE "curves" IS 'curves.csv minus country (duplicates the currency → country hop).';

COMMENT ON COLUMN "curves"."aliases" IS 'curated other names ("CVD govt curve")';

COMMENT ON COLUMN "curves"."currency" IS 'DENOMINATED_IN hop: curve → currency';

CREATE TABLE "instruments" (
  "instrument_id" text PRIMARY KEY,
  "isin" char(12) UNIQUE,
  "ticker" text UNIQUE NOT NULL,
  "description" text NOT NULL,
  "aliases" text[] NOT NULL DEFAULT '{}',
  "instrument_type" text NOT NULL,
  "issuer_name" text,
  "issuer_id" text,
  "guarantor_name" text,
  "guarantor_id" text,
  "currency" char(3) NOT NULL,
  "underlying_curve" text,
  "source_system" text NOT NULL,
  "source_file" text NOT NULL,
  "updated_on" date NOT NULL
);

COMMENT ON TABLE "instruments" IS 'instruments.csv minus coupon, maturity, plus the resolved issuer_id and guarantor_id. Issuer, guarantor, currency and curve are not copied into statements; the edges view projects them.';

COMMENT ON COLUMN "instruments"."isin" IS 'position resolution when ref_type = ISIN';

COMMENT ON COLUMN "instruments"."ticker" IS 'position resolution when ref_type = TICKER';

COMMENT ON COLUMN "instruments"."aliases" IS 'curated other names ("CDB 27s", "3M NDFs"); GIN index';

COMMENT ON COLUMN "instruments"."instrument_type" IS 'CDS → REFERENCES_CREDIT instead of ISSUED_BY';

COMMENT ON COLUMN "instruments"."issuer_name" IS 'as written by SecMaster; the evidence for issuer_id and the quote on the ISSUED_BY edge';

COMMENT ON COLUMN "instruments"."issuer_id" IS 'resolved at load through the alias view; null = UNRESOLVED_NAME flag. ISSUED_BY edge (REFERENCES_CREDIT for a CDS)';

COMMENT ON COLUMN "instruments"."guarantor_name" IS 'as written; the evidence for guarantor_id';

COMMENT ON COLUMN "instruments"."guarantor_id" IS 'resolved at load; GUARANTEED_BY edge';

COMMENT ON COLUMN "instruments"."currency" IS 'DENOMINATED_IN hop';

COMMENT ON COLUMN "instruments"."underlying_curve" IS 'PRICED_OFF hop';

CREATE TABLE "ownership" (
  "ownership_id" serial PRIMARY KEY,
  "owner" text NOT NULL,
  "owner_id" text,
  "owned_entity" text NOT NULL,
  "owned_id" text,
  "stake_pct" numeric(5,2) NOT NULL,
  "as_of_date" date NOT NULL,
  "source" text,
  "notes" text,
  "source_file" text NOT NULL,
  "updated_on" date NOT NULL
);

CREATE UNIQUE INDEX ON "ownership" ("owner", "owned_entity", "as_of_date");

COMMENT ON TABLE "ownership" IS 'ownership.csv, the tracker spreadsheet, plus resolved ids. Tier 2. Its rows are OWNS edges projected by the edges view (status REFERENCE); the two phrases in notes become INFERRED statements.';

COMMENT ON COLUMN "ownership"."owner" IS 'as written by the tracker; evidence for owner_id';

COMMENT ON COLUMN "ownership"."owner_id" IS 'resolved at load through the alias view';

COMMENT ON COLUMN "ownership"."owned_entity" IS 'as written; evidence for owned_id';

COMMENT ON COLUMN "ownership"."owned_id" IS 'resolved at load. owner_id → owned_id is the OWNS edge, tier 2, dated as_of_date';

COMMENT ON COLUMN "ownership"."stake_pct" IS '0–100';

COMMENT ON COLUMN "ownership"."as_of_date" IS 'the date the stake was true; the PIT question turns on it';

COMMENT ON COLUMN "ownership"."source" IS 'the citation given by the tracker (annual report, charter, prospectus)';

COMMENT ON COLUMN "ownership"."notes" IS 'two rules read it: "sovereign guarantee" → GUARANTEED_BY, "Financing vehicle" → FINANCING_VEHICLE_OF';

CREATE TABLE "ratings" (
  "entity" text NOT NULL,
  "issuer_id" text,
  "agency" text NOT NULL,
  "rating" text NOT NULL,
  "outlook" text NOT NULL,
  "action_date" date NOT NULL,
  "source" text NOT NULL,
  "source_file" text NOT NULL,
  "updated_on" date NOT NULL,
  PRIMARY KEY ("entity", "agency", "action_date")
);

COMMENT ON TABLE "ratings" IS 'ratings.csv, an event log, plus the resolved issuer_id. (agency, rating) must exist in rating_scale. Not copied into statements.';

COMMENT ON COLUMN "ratings"."entity" IS 'as written by the feed; evidence for issuer_id';

COMMENT ON COLUMN "ratings"."issuer_id" IS 'resolved at load through the alias view';

CREATE TABLE "positions" (
  "book" text NOT NULL,
  "instrument_ref" text NOT NULL,
  "ref_type" "ref_type" NOT NULL,
  "quantity" numeric(18,2) NOT NULL,
  "notional_ccy" char(3) NOT NULL,
  "as_of_date" date NOT NULL,
  "source_file" text NOT NULL,
  "updated_on" date NOT NULL,
  PRIMARY KEY ("book", "instrument_ref", "as_of_date")
);

COMMENT ON TABLE "positions" IS 'positions_<date>.csv. Resolved to instruments by ref_type in the position_resolved view; an unresolved ref is reported, never guessed.';

COMMENT ON COLUMN "positions"."book" IS 'RLS: role book_<book>';

COMMENT ON COLUMN "positions"."quantity" IS 'sign convention undocumented; reported as-is';

-- ------------------------------------------------------------------------------------------------------------
-- Level 3 · documents (one table; declared before statements, which point at them)
-- ------------------------------------------------------------------------------------------------------------

CREATE TABLE "documents" (
  "document_id" serial PRIMARY KEY,
  "source_system" text NOT NULL,
  "source_file" text NOT NULL,
  "kind" "doc_kind" NOT NULL,
  "title" text,
  "publisher" text,
  "author" text,
  "published_at" timestamp NOT NULL,
  "visibility" text,
  "text" text NOT NULL,
  "about_issuers" text[] NOT NULL DEFAULT '{}',
  "about_instruments" text[] NOT NULL DEFAULT '{}',
  "about_curves" text[] NOT NULL DEFAULT '{}',
  "about_currencies" text[] NOT NULL DEFAULT '{}',
  "topics" text[] NOT NULL DEFAULT '{}',
  "summary" text,
  "annotated_by" "annotator" NOT NULL,
  "updated_on" date NOT NULL
);

CREATE UNIQUE INDEX "documents_unique" ON "documents" ("source_file", "published_at", (coalesce(author, '')));

CREATE INDEX ON "documents" ("about_issuers");

CREATE INDEX ON "documents" ("about_instruments");

COMMENT ON TABLE "documents" IS 'Level 3 is this one table. One row per research note; one row per desk-chat line.
Two annotators fill the same about_* columns: the alias scan at load (RULE: deterministic, no key needed) and,
where available, the LLM annotator (LLM: every id it names must resolve through the alias view, else it is dropped and
reported; it also writes summary and topics). "Research about X" is `where X = any(about_<type>)`.
Relationships found in the text are not stored here: they are PROPOSED rows in statements with document_id set.';

COMMENT ON COLUMN "documents"."source_system" IS 'ResearchHub | DeskNotes: keeps the two datasets distinguishable inside one table';

COMMENT ON COLUMN "documents"."author" IS 'desk notes: the chat handle';

COMMENT ON COLUMN "documents"."published_at" IS 'desk notes: the bracketed time of the line';

COMMENT ON COLUMN "documents"."visibility" IS 'external | macro_internal | credit_internal; null = hidden from everyone. RLS: role vis_<label>';

COMMENT ON COLUMN "documents"."text" IS 'the source of every quote and the only thing cited';

COMMENT ON COLUMN "documents"."about_issuers" IS 'issuer ids the document is about; GIN index';

COMMENT ON COLUMN "documents"."about_instruments" IS 'instrument ids';

COMMENT ON COLUMN "documents"."about_curves" IS 'curve ids';

COMMENT ON COLUMN "documents"."about_currencies" IS 'currency codes';

COMMENT ON COLUMN "documents"."topics" IS 'downgrade, guarantee, ownership, FX, ...';

COMMENT ON COLUMN "documents"."summary" IS 'one line, LLM-written; a pointer to the document, never a citation';

COMMENT ON COLUMN "documents"."annotated_by" IS 'which annotator wrote the about_* columns';

-- ------------------------------------------------------------------------------------------------------------
-- Level 2 · predicates, statements
-- ------------------------------------------------------------------------------------------------------------

CREATE TABLE "predicate_def" (
  "predicate" text PRIMARY KEY,
  "single_valued" boolean NOT NULL,
  "compare" "compare" NOT NULL,
  "direction" "direction" NOT NULL,
  "description" text NOT NULL
);

COMMENT ON TABLE "predicate_def" IS 'The model as code. Fourteen rows:
ISSUED_BY, REFERENCES_CREDIT, GUARANTEED_BY, FINANCING_VEHICLE_OF, OWNS, COUNTRY_OF_RISK, RATING_CAPPED_BY,
TRADES_AS_PROXY_FOR, BETA_TO, CORRELATED_WITH (statements);
DENOMINATED_IN, PRICED_OFF, CURRENCY_OF, SOVEREIGN_IS (level-1 columns projected by the edges view).';

COMMENT ON COLUMN "predicate_def"."single_valued" IS 'true: two different objects on the same subject disagree';

COMMENT ON COLUMN "predicate_def"."compare" IS 'what two rows on the same link are compared on';

COMMENT ON COLUMN "predicate_def"."direction" IS 'how a path walks it; OWNS is walked owned → owner';

CREATE TABLE "statements" (
  "statement_id" serial PRIMARY KEY,
  "subject_type" text NOT NULL,
  "subject_id" text NOT NULL,
  "predicate" text NOT NULL,
  "object_type" text NOT NULL,
  "object_id" text NOT NULL,
  "value_num" numeric(12,4),
  "value_text" text,
  "holds" boolean NOT NULL DEFAULT True,
  "as_of" date NOT NULL,
  "source_system" text NOT NULL,
  "source_file" text NOT NULL,
  "document_id" int,
  "quote" text,
  "method" "method" NOT NULL,
  "status" "status" NOT NULL,
  "visibility" text,
  "updated_on" date NOT NULL
);

CREATE UNIQUE INDEX "statements_unique" ON "statements" ("subject_type", "subject_id", "predicate", "object_id", "as_of", "source_file", (coalesce(quote, '')));

CREATE INDEX "statements_subject" ON "statements" ("subject_type", "subject_id", "predicate");

CREATE INDEX "statements_object" ON "statements" ("object_type", "object_id", "predicate");

COMMENT ON TABLE "statements" IS 'A link that no file column holds: produced by a rule or read from a document. One row per link per source.
Nothing is overwritten: a newer value is a new row. Links a file column does hold (issuer_id, guarantor_id,
owner_id → owned_id, currency, curve, country → sovereign) are not copied here; the edges view projects them.
INFERRED: a rule over tier-3/tier-2 data (country of incorporation, the vehicle rule, ownership.notes). Ranks with REFERENCE.
PROPOSED: from a document (hand-curated or LLM-extracted). Never current when a reference-grade row exists on the link; it flags (STALE, CONFLICT) and is returned beside the winner.
CONFIRMED / REJECTED: the decision of a person on a PROPOSED row.';

COMMENT ON COLUMN "statements"."statement_id" IS 'the citation id';

COMMENT ON COLUMN "statements"."subject_type" IS 'issuer | instrument | unresolved';

COMMENT ON COLUMN "statements"."object_type" IS 'issuer | country | currency | curve';

COMMENT ON COLUMN "statements"."value_num" IS 'stake %, beta, correlation';

COMMENT ON COLUMN "statements"."value_text" IS 'qualifier, e.g. "indirect via holding"';

COMMENT ON COLUMN "statements"."holds" IS 'false records a denial; never walked';

COMMENT ON COLUMN "statements"."as_of" IS 'when the link was true, not when it was published';

COMMENT ON COLUMN "statements"."source_system" IS 'tier for precedence';

COMMENT ON COLUMN "statements"."source_file" IS 'the file or document the row came from';

COMMENT ON COLUMN "statements"."document_id" IS 'null for rows from datasets and rules';

COMMENT ON COLUMN "statements"."quote" IS 'verbatim sentence from documents.text, or the rule that produced the row';

COMMENT ON COLUMN "statements"."visibility" IS 'copied from the document so the RLS policy needs no join; null = everyone';

ALTER TABLE "country" ADD FOREIGN KEY ("sovereign_issuer_id") REFERENCES "issuers" ("issuer_id");

ALTER TABLE "issuers" ADD FOREIGN KEY ("country_of_incorporation") REFERENCES "country" ("code");

ALTER TABLE "issuers" ADD FOREIGN KEY ("source_system") REFERENCES "sources" ("source_id");

ALTER TABLE "curves" ADD FOREIGN KEY ("source_system") REFERENCES "sources" ("source_id");

ALTER TABLE "instruments" ADD FOREIGN KEY ("issuer_id") REFERENCES "issuers" ("issuer_id");

ALTER TABLE "instruments" ADD FOREIGN KEY ("guarantor_id") REFERENCES "issuers" ("issuer_id");

ALTER TABLE "instruments" ADD FOREIGN KEY ("underlying_curve") REFERENCES "curves" ("curve_id");

ALTER TABLE "instruments" ADD FOREIGN KEY ("source_system") REFERENCES "sources" ("source_id");

ALTER TABLE "ownership" ADD FOREIGN KEY ("owner_id") REFERENCES "issuers" ("issuer_id");

ALTER TABLE "ownership" ADD FOREIGN KEY ("owned_id") REFERENCES "issuers" ("issuer_id");

ALTER TABLE "ratings" ADD FOREIGN KEY ("issuer_id") REFERENCES "issuers" ("issuer_id");

ALTER TABLE "ratings" ADD FOREIGN KEY ("source") REFERENCES "sources" ("source_id");

ALTER TABLE "ratings" ADD FOREIGN KEY ("agency", "rating") REFERENCES "rating_scale" ("agency", "rating");

ALTER TABLE "documents" ADD FOREIGN KEY ("source_system") REFERENCES "sources" ("source_id");

ALTER TABLE "statements" ADD FOREIGN KEY ("predicate") REFERENCES "predicate_def" ("predicate");

ALTER TABLE "statements" ADD FOREIGN KEY ("source_system") REFERENCES "sources" ("source_id");

ALTER TABLE "statements" ADD FOREIGN KEY ("document_id") REFERENCES "documents" ("document_id");

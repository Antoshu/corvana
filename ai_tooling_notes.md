# How I used AI coding tools

I used Claude Code throughout, as two sessions with different jobs:

- **A design session** (Claude Fable) that I worked with directly: it drafted the schema, the ground truth, the
  expected answers, the briefs and the write-up, and it reviewed the implementation session's output. Everything in
  `model/`, `tests/expected/` and the narrative went through it, and most of my corrections below were made to it.
- **An implementation session** (Claude Opus) that only ever received written briefs: schema generation, loader,
  tools, MCP server, agent, annotator, ingest, tests. Each brief named the files it owned and nothing else, the
  expected row counts after load, the expected-answer files as the contract, and the rule "report, don't fix": a
  discrepancy is reported back, an expectation is never edited to make a test pass. It reported every hand-written
  SQL change explicitly, and every judgement call it made where the brief was silent, for me to accept or override.

The two sessions talked to each other by message; I only talked to the design session. That split kept the model's
"I'll just fix the test" instinct out of the contract files, and it meant every change had a written reason before
it was made. The design session kept a dated log of my comments and decisions as we went; the ones that matter are
summarised below.

## Things the tools suggested that I changed or rejected

1. **SQLite instead of Postgres.** Proposed early on because the brief only requires entitlements inside the
   tools and the demo would need nothing running. Rejected: I wanted for it to be an option for users to query this layer directly, so
   security had to be implemented "below" the MCP.

2. **Confirmed facts as columns on `issuers`.** An earlier design copied `guaranteed_by`, `sovereign_beta`,
   `trades_as_sovereign_proxy` onto the issuer row. Rejected after noticing it hides data quality: a column cannot
   say that CPL's beta came from one credit-internal note that one PM cannot read. Replaced by the statements table
   with provenance on every row.

3. **Letting newer research overrule reference data.** The first draft of the expected answer had bob's CPL stake
   resolve to 34% because the internal note was newer than the tracker. Changed: a lower-trust source can flag a
   reference value as stale, it cannot replace it. The answer is both numbers with both dates.

4. **Loading source tables with every column, as delivered.** The model argued for keeping sector, issuer type,
   LEI, coupon and maturity so the files stay reproducible, and LEI for firm scale. Rejected: the brief says "only
   those", and a column no query reads is weight, not reproducibility. The schema was rebuilt from the question
   outward with a written ground truth and a verdict per column.

5. **A test that the SQL and the DBML agree.** Proposed to close the gap between the two schema files. I preferred
   to derive the SQL from the DBML so the table schema is never written by hand at all; the test now checks that the
   committed generated file matches a fresh generation.

Two more passes came from the tools themselves, both after the proof of concept was "done": an ingest stress test
(the real delta plus twelve synthetic deliveries on a copy of the database) found six defects that changed answers, the worst being
that a back-dated delivery changed a past answer and that a partial positions file hid a whole book; and a
separate code-review session found eight more, the worst being that the path walk ignored a person's confirmation
and that the hidden-count function trusted a caller-supplied user name. All were fixed with regression tests. One
proposed fix I changed: the review's "walk only the winning row" would have removed the unconfirmed desk-view
channel the design wants shown, so the rule became "a person's confirmation settles the link; until then every row
is walkable at its own grade".

## Key prompts and excerpts

The instruction that shaped the whole build, given to the design session after two days of documents and no code:

> Start from the final output: the PM question, the agent, the MCP call carrying the user's intent and permissions,
> the structured data with links and metadata for tracing. Write the expected answers for alice and bob by hand
> before any code; they are the contract.

The delegation rule:

> For any kind of easy implementation, delegate to the implementation session. Clearly delimited tasks like code
> writing, ingestion, SQL can be done by it. You own the design, the expected answers and the review.

The opening of the rework brief sent to the implementation session (the rest listed nine numbered deliverables):

> Read first, in this order: CLAUDE.md, model/ground_truth.md, model/table_review.md, model/schema.dbml,
> tests/expected/*.md. Those files are the truth; where the current code disagrees with them, the code changes.
> Do not edit anything under model/, tests/expected/, narrative.md, decisions.md or CLAUDE.md; report
> discrepancies to me instead. [...] If your counts differ, report, do not force.

(`decisions.md` was the design session's dated log; it was folded into this note and `narrative.md` and then deleted.)

An excerpt of the implementation session reporting rather than fixing, which is the behaviour the briefs asked for:

> WHERE THE EXPECTED / TRUTH FILES LOOK WRONG (not changed): alice_exposure.md says the macro note is about
> INS-1004 via about_instruments. Neither the alias scan nor the model tags INS-1004: the note says "the 2033", a
> name aliases.yaml deliberately leaves out. Either add "the 2033" as an alias or soften the expectation.

That one became the grounding redesign: the right answer was neither a global alias nor a softer test, but a
model that can resolve "the 2033" from context and quote the evidence.

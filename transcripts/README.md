# Transcripts

Generated files; every one is reproduced by the commands in the root `README.md` against a fresh `kl-load`.

- `agent_<user>_<question>.md` (Part 2): the Claude agent (`kl-agent`) over the eight tools. Each tool call with
  its JSON result, then an **Answer** section at the end, which is the part a portfolio manager reads; the calls
  above it are the evidence that every claim in the answer came from a tool. alice and bob get different answers
  from the same question because Postgres shows each of them different rows.
- `annotate.md`: the grounded annotation run (`kl-annotate --all`): per document, the alias-scan mentions, the
  model's choice and confidence for each, what was kept or dropped and why.
- `update_<date>.md` (Part 3): the ingest report (`kl-update`): what the delta applied, what it discarded and why,
  how the new note was annotated, and which data-quality flags opened or closed.
- `agent_bob_corvana-was-downgraded-to-b-yesterday.md` (Part 3): the agent asked again as of 2026-10-28, after the
  delta, so the effect of the ingest on the answer is visible: the new CNOC bond, the B+ ratings, the CDB rating lag,
  the closed unresolved ref, and Bank B's new note.

`kl-demo` (scripted tool calls, no LLM) still exists as an offline fallback and writes the same kind of file; its
output is not part of the submission.

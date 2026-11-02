# Knowledge Engineer – Take-Home Task

## The scenario

A portfolio manager asks:

> *"If the Republic of Corvana is downgraded, what in my book is exposed, how, and what does our research say about it?"*

Answering well means joining things no single system links together: the sovereign's own bonds, its rates curve
and currency, state-linked companies whose debt trades with the sovereign, and research and desk opinion about all of
them. Sources name the same things differently. Some links exist only in documents or in people's heads. Some
information is out of date or contradicts other information. And two PMs asking the same question should get different
answers, because they can see different books and research.

Your task is to build a **small, working knowledge layer** for this scenario and the **tools an AI agent would use**
to answer questions like this, with every answer traceable to its sources.

All entities, identifiers and data in the pack are **fictional**. Identifiers use real formats (ISIN, LEI). Country
code `QC` and currency `CVD` are made up. This is deliberate: answers should come from the data, not from a model's
general knowledge.

## The data pack

```
data/
  reference/      issuers, instruments, ownership, ratings, curves   (structured, mostly reliable)
  positions/      end-of-day positions for two books                  (structured)
  research/       broker and internal research notes                  (unstructured, point-in-time opinion)
  desk_notes/     informal desk notes copied from chat                (unstructured, expert opinion)
  entitlements.yaml   which users can see which books and research
  sources.yaml        the source systems, their owners and how reliable they are
  updates/2026-10-28/ data that arrived the next day (Part 3)
```

The data is as of close of business on **2026-10-27**; treat that as "today". `data/README.md` describes the
positions file. The data is realistic, so it is imperfect. Part of the task is deciding what to do about that.

## What we'd like you to do

This is deliberately open-ended. We care more about your judgement on what to build, and why, than about how much
you build. A small thing that works and that you can explain beats a large thing that doesn't.

### Part 1 – Model and build the layer

- Design a knowledge model covering the entities and relationships you need for this scenario, and **only** those.
- Load the data pack into it, resolving identities across sources (the same issuer, instrument or concept may appear
  under different names or identifiers).
- Record where each fact and link came from, and when it was true.
- Manage the model as code, with some automated validation.

Use any storage or graph technology you like, such as Neo4j, an RDF store, networkx, SQLite, DuckDB or Postgres.
Tell us why you chose it.

### Part 2 – Tools for agents

- Build a small set of well-defined, typed tools an AI agent would call to find entities, retrieve knowledge and follow
  relationships. Exposing them as an MCP server is welcome but not required.
- Enforce entitlements **inside** the tools, not in the agent's prompt.
- Show the tools answering the PM's question for **alice** and for **bob** (see `entitlements.yaml`), with sources
  cited. An LLM-driven agent is ideal. If you don't have API access, a scripted sequence of tool calls is fine. Say
  which you did.
- Show at least one point-in-time question, for example: *what was the state's stake in Corvana Power & Light on
  2025-06-30, and what is it now?*

### Part 3 – Keeping it current

The files in `updates/2026-10-28/` arrived the next day. Show how your layer takes them in. Which changes would you
apply automatically, which would you propose for a person to confirm, and which would you flag as stale or
conflicting? An agent-driven approach is welcome, but a clear design with a partial implementation is fine.

### Part 4 – Short write-up (max 3 pages)

Cover:

1. Your model: what you modelled, what you deliberately left out, and why.
2. How you resolved identities and handled conflicting or stale information.
3. Where you used deterministic methods and where (if anywhere) you used an LLM, and why.
4. How you would measure whether the layer is accurate and whether it improves AI answers. Include a handful of test
   questions with expected answers, ideally runnable.
5. What you would do next with another two weeks, and what would change at the scale of the whole firm.

## What to send us

- A git repository (zip or link) with a README explaining how to run it in a few commands.
- Your write-up (Markdown or PDF).
- Sample output or transcripts from Parts 2 and 3.
- A short note on how you used AI coding tools. We expect you to use them. Include at least three things they
  suggested that you changed or rejected, and why. A few of your key prompts or transcript excerpts are welcome but
  optional.

## Time

Please spend **no more than 4 hours**. We won't reward going beyond that, and we are not looking for polish. If time
is short, prioritise Parts 1, 2 and 4, and treat Part 3 as design only. If you run out of time, write down what you would have done next; that is
useful to us. Python is preferred, but use what you're most productive in.

You may use any LLM provider. Please don't include API keys or other credentials in your submission.

## What happens next

We'll ask you to walk us through your submission in a 60-minute session. We'll then give you some new data and ask you
to work through it with your solution, live with us. Please have your solution running on your machine for the call.
You can use AI tools during the session, as you would at work.

If anything in the brief is unclear, make a reasonable assumption and write it down. Handling ambiguity is part of the
job.

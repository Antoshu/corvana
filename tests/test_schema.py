"""010_tables.sql is build output of model/schema.dbml: a fresh generation must equal the committed file."""
from __future__ import annotations

from kl import config
from kl.schema_gen import generate


def test_tables_sql_matches_dbml():
    committed = config.SCHEMA_FILES[0].read_text(encoding="utf-8")
    assert committed == generate(), "run `uv run kl-schema`; 010_tables.sql is never edited by hand"


def test_generated_shape():
    text = generate()
    assert text.startswith("-- generated from model/schema.dbml by kl-schema; do not edit")
    assert text.count("CREATE TABLE ") == 13
    assert text.count("ADD FOREIGN KEY") == 17
    assert text.count("CREATE TYPE ") == 7
    for gone in ("alias", "document_mentions", "extraction_review", "ingest_log", "pending_changes", "rating_agency"):
        assert f'CREATE TABLE "{gone}"' not in text

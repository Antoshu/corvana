"""kl-schema: generate src/kl/db/010_tables.sql from model/schema.dbml.

The DBML is the model; the SQL file is build output, committed so the loader and the tests need no parser at run
time. Every ref is emitted as ALTER TABLE ... ADD FOREIGN KEY after all tables, so table order and the
country <-> issuers cycle do not matter. tests/test_schema.py fails when the committed file differs from a fresh
generation.
"""
from __future__ import annotations

import sys
from pathlib import Path

from pydbml import PyDBML

from kl import config

HEADER = "-- generated from model/schema.dbml by kl-schema; do not edit\n\n"


def generate(dbml_path: Path = config.DBML) -> str:
    db = PyDBML(dbml_path)
    for ref in db.refs:
        ref.inline = False
    return HEADER + db.sql.replace("\r\n", "\n").rstrip() + "\n"


def main() -> None:
    out = config.SCHEMA_FILES[0]
    text = generate()
    if "--check" in sys.argv[1:]:
        same = out.is_file() and out.read_text(encoding="utf-8") == text
        print(f"{out} {'matches' if same else 'DIFFERS FROM'} {config.DBML}")
        sys.exit(0 if same else 1)
    out.write_text(text, encoding="utf-8", newline="\n")
    tables = text.count("CREATE TABLE ")
    fks = text.count("ADD FOREIGN KEY")
    enums = text.count("CREATE TYPE ")
    print(f"wrote {out}: {tables} tables, {fks} foreign keys, {enums} enum types")


if __name__ == "__main__":
    main()

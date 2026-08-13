"""Regenerate ``stubs/iso4217/__init__.pyi``. Run via ``just stubs``.

``iso4217`` ships ``py.typed`` and a stub, but the stub declares
``class Currency(enum.Enum)`` with only its methods and properties -- no members.
The enum is built at runtime from ``table.xml`` through the functional Enum API,
and a type checker reads source rather than runtime state, so every
``Currency.USD`` looks like an unknown attribute.

This copies the upstream stub and inserts the 178 member declarations. A local
stub shadows the installed one completely, which is why the rest is copied
verbatim instead of being extended.

The real fix belongs upstream; this keeps the repository checkable meanwhile.
"""

from __future__ import annotations

import pathlib

import iso4217
from iso4217 import Currency

HEADER = """\
# Stub for `iso4217`, overriding the one shipped upstream.
#
# The upstream stub declares `class Currency(enum.Enum)` with its methods and
# properties but no members: the enum is built at runtime from table.xml via the
# functional Enum API, so a type checker -- which reads source, not runtime state
# -- sees every `Currency.USD` as an unknown attribute.
#
# A local stub shadows the installed one entirely, so everything below the member
# list is copied verbatim from upstream and must stay complete.
#
# Generated from iso4217 {version}. Do not edit by hand; run `just stubs`.
"""

ANCHOR = "class Currency(enum.Enum):\n"
OUTPUT = pathlib.Path("stubs/iso4217/__init__.pyi")


def main() -> None:
    upstream = pathlib.Path(iso4217.__file__).with_suffix(".pyi")
    if not upstream.is_file():
        raise SystemExit(f"upstream stub not found at {upstream}")

    source = upstream.read_text()
    if ANCHOR not in source:
        raise SystemExit(
            f"{upstream} no longer declares {ANCHOR.strip()!r}; "
            "the upstream stub changed shape and this script needs updating"
        )

    members = "\n".join(f"    {member.name}: Currency" for member in Currency)
    body = source.replace(ANCHOR, ANCHOR + members + "\n", 1)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(HEADER.format(version=iso4217.__version__) + "\n" + body)
    print(f"wrote {OUTPUT} with {len(list(Currency))} members")


if __name__ == "__main__":
    main()

set dotenv-load

# Run bank client tests: all, mono, mono-live, pb, or nbu.
test suite="all":
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{ suite }}" in
      all)
        uv run python -m unittest discover -s tests -v
        ;;
      mono)
        uv run python -m unittest discover -s tests -p 'test_monobank.py' -v
        ;;
      mono-live)
        : "${MONO_TOKEN:?MONO_TOKEN must be set in .env}"
        MONOBANK_LIVE_TESTS=1 uv run python -m unittest discover -s tests -p 'test_monobank_live.py' -v
        ;;
      pb)
        uv run python -m unittest discover -s tests -p 'test_privatbank.py' -v
        ;;
      nbu)
        uv run python -m unittest discover -s tests -p 'test_nbu.py' -v
        ;;
      *)
        echo "Unknown test suite '{{ suite }}'. Expected: all, mono, mono-live, pb, or nbu." >&2
        exit 2
        ;;
    esac

# Releases are published by .github/workflows/python-publish.yml when a GitHub
# release is published: Trusted Publishing with PEP 740 attestations. There is
# deliberately no local publish -- an unattested upload is indistinguishable
# from one made with a stolen token.

# Audit uv.lock for known vulnerabilities (OSV), as the CI audit does.
# The ignored tornado advisories are fixed only in 6.6, which dropped Python
# 3.10; they hit the dev-only 3.10 branch. Keep in sync with audit.yml.
audit:
    uv audit --locked --preview-features audit-command \
        --ignore GHSA-pcg2-g6cj-q92c \
        --ignore GHSA-pw9p-v7r6-gx4p \
        --ignore GHSA-r4j5-9xpp-3985

lint:
    uv run ruff check . --fix
    uv run ty check .

format:
    uv run ruff format .

# Regenerate stubs/iso4217/__init__.pyi from the installed package.
# Run after bumping iso4217; the member list tracks its table.xml.
stubs:
    uv run python scripts/generate_iso4217_stub.py

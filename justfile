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

publish:
    uv build
    uv publish --username "$PYPI_USERNAME" --password "$PYPI_PASSWORD"

lint:
    uv run ruff check . --fix
    uv run ty check .

# Regenerate stubs/iso4217/__init__.pyi from the installed package.
# Run after bumping iso4217; the member list tracks its table.xml.
stubs:
    uv run python scripts/generate_iso4217_stub.py

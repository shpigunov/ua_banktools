set dotenv-load

publish:
  uv build
  uv publish --username "$PYPI_USERNAME" --password "$PYPI_PASSWORD"

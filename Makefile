ifneq (,$(wildcard ./.env))
	include .env
	export
endif

publish:
	uv build
	uv publish --username ${PYPI_USERNAME} --password ${PYPI_PASSWORD}

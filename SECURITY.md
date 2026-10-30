# Security policy

## Supported versions

Only the latest minor release receives security fixes.

| Version | Supported |
| ------- | --------- |
| 0.4.x   | Yes       |
| < 0.4   | No        |

## Reporting a vulnerability

Please report vulnerabilities privately through
[GitHub's private vulnerability reporting](https://github.com/shpigunov/ua_banktools/security/advisories/new),
not in a public issue.

This library handles bank API tokens and account data, so reports about
credentials or response data leaking (into logs, exceptions, serialized
models, or requests sent to the wrong host) are especially welcome.

You can expect an acknowledgement within a week. Confirmed issues are fixed in
a new release and disclosed through a GitHub Security Advisory, which also
feeds the OSV database that PyPI and `uv audit` read.

## Verifying releases

From 0.4.0 on, every release is built and published by
[`python-publish.yml`](.github/workflows/python-publish.yml) through PyPI
Trusted Publishing, with PEP 740 attestations. To check that a downloaded file
came from this repository's workflow:

```bash
uvx pypi-attestations verify pypi \
  --repository https://github.com/shpigunov/ua_banktools \
  'pypi:ua_banktools-0.4.0-py3-none-any.whl'
```

Releases before 0.4.0 were uploaded with an API token and carry no
attestations.

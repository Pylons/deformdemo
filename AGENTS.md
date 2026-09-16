# AGENTS.md — deformdemo

Run these checks before considering work done. They mirror `.github/workflows/ci-tests.yml`
(invoked via `tox`). All commands run from the repo root.

## Fast pre-check (run first)

```sh
ruff check                  # line-length 79, excludes bootstrap.py (config in pyproject.toml)
```

`bootstrap.py` is a generated zc.buildout script (Zope Foundation); it is outside the CI
lint scope (CI lints `deformdemo setup.py`, not the repo-root bootstrap script) and is
excluded from ruff.

## Lint (CI: `tox -e lint`, basepython python3.11)

```sh
flake8 deformdemo setup.py
isort --check-only --diff deformdemo setup.py
black --check --diff deformdemo setup.py
python setup.py check -r -s -m
check-manifest
```

- `black` / `isort` / `flake8` line-length: **79** (see `pyproject.toml` `[tool.black]`, `[tool.isort]`, `.flake8`).
- Lint scope is the `deformdemo/` package **and** `setup.py` (not `bootstrap.py`).

## Tests (CI: `tox -e py`)

Functional/Selenium tests run against a live server via `tox.sh`:

```sh
pserve demo.ini &           # started by tox.sh
pytest "$@"                 # functional suite (needs selenium + Firefox; URL env set by CI)
```

Requires a running Selenium standalone-firefox (CI sets `URL=http://<host>:8523`,
`DISPLAY`, `WEBDRIVER`). Skip unless working on functional tests.

## Notes

- Supported Python: 3.10–3.13 + PyPy 3.10 (see CI matrix).
- `deformdemo` depends on `deform` from git (`requirements-dev.txt`); changes to deform
  often need a matching demo change here.
- `setup.cfg [tool:pytest]` uses `python_files = test.py`, `testpaths = .`, `addopts = -W always`.

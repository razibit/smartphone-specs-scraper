# Contributing

Thank you for helping improve MobileDokan Scraper. Contributions are welcome for parsing fixes, reliability improvements, tests, documentation, and data-export behavior.

## Before you start

- Check existing issues and pull requests for related work.
- For parser changes, include a small representative HTML fixture when possible.
- Do not commit cookies, access tokens, personal data, scraped logs, or generated output files.
- Confirm that your proposed requests and usage comply with MobileDokan's published policies and applicable law.

## Local setup

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Checks before submitting a change

```bash
python -m compileall -q main.py mobiledokan_scraper tests
python -m pytest
python -m pytest --cov=mobiledokan_scraper --cov-report=term-missing
```

The default test command uses local fixtures and mocks. The live network test is opt-in:

```bash
python -m pytest -m live
```

## Code and documentation expectations

- Keep responsibilities separated between HTTP access, listing extraction, detail parsing, validation, and export.
- Preserve the existing JSON/CSV field names unless a schema change is intentional and documented.
- Keep request delays, retries, and backoff respectful; do not add concurrency that could increase load on the source site without discussion.
- Add or update tests for every behavior change.
- Update `README.md`, `docs/usage.md`, or `docs/data_structure.md` when commands, configuration, or output fields change.

## Pull requests

A pull request should explain the user-facing result, identify the affected modules, and include the checks that were run. If a change depends on the current MobileDokan HTML structure, describe the selectors or source markup involved.


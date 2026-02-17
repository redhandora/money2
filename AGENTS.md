# AGENTS.md

Guidance for agentic coding assistants working in this repository.

## Environment
- Project: `phase1-youtube-trending-shorts`
- Python: `>=3.6` (`pyproject.toml`)
- Layout: `src/` package layout (`src/phase1_youtube`)
- Test framework: `pytest` (`[tool.pytest.ini_options]`)

## Machine Constraints
- This machine has 2 CPU cores.
- Do not over-parallelize subagents.
- Prefer 1-2 concurrent heavy tasks max.

## Rule Files Check
- `.cursor/rules/`: not present
- `.cursorrules`: not present
- `.github/copilot-instructions.md`: not present

If any of these are added later, treat them as higher-priority constraints.

## Setup
Install dependencies:

```bash
python -m pip install -e .
python -m pip install -e .[dev]
```

Notes:
- Runtime dep: `google-api-python-client`
- Dev dep: `pytest>=6.2.5`
- `tests/conftest.py` injects `src/` into `sys.path` for tests.

## Build / Lint / Test / Run

### Tests
Run full suite:

```bash
pytest -q
```

Run a single test file:

```bash
pytest -q tests/test_ingest.py
```

Run a single test case:

```bash
pytest -q tests/test_ingest.py::test_main_offline_fixtures_writes_jsonl_and_manifest
```

Run by keyword:

```bash
pytest -q -k "validate_output or schema"
```

### Pipeline commands
Offline run:

```bash
PYTHONPATH=src python -m phase1_youtube.ingest --regions JP,US --top-n 2 --offline-fixtures tests/fixtures --out output/run.jsonl
```

Validate output:

```bash
PYTHONPATH=src python -m phase1_youtube.validate_output --input output/run.jsonl
```

Live-path error reproduction (missing key):

```bash
env -u YOUTUBE_API_KEY PYTHONPATH=src python -m phase1_youtube.ingest --regions JP,US --top-n 2 --out output/live-no-key.jsonl
```

### Build and lint status
- No dedicated build command is defined.
- No canonical lint command is configured (`ruff/flake8/black/isort/mypy` configs absent).
- Follow existing source style and rely on tests for verification.

## Code Style (Observed)

### Imports
- Use stdlib imports first, then local package imports.
- Keep one blank line between import groups.
- Prefer absolute imports from `phase1_youtube`.

### Formatting
- Use 4-space indentation.
- Preserve multiline call style with trailing commas.
- Existing code mostly uses `.format(...)` for dynamic messages.
- f-strings exist in limited places; do not mass-refactor style only.

### Typing
- Typing is selective, not strict across all modules.
- Use Python 3.6-compatible typing forms (`Dict`, `Optional`, `Mapping`).
- Avoid syntax/features requiring newer Python without compatibility updates.

### Naming
- `snake_case` for functions/variables.
- `UPPER_SNAKE_CASE` for constants.
- `CapWords` for classes and exceptions.
- Prefix internal helpers/private classes with `_`.

## Error Handling Expectations
- Validate inputs explicitly and raise deterministic errors.
- Keep error messages stable; tests assert exact strings/regex.
- CLI `main()` should print `ERROR: ...` to stderr and return non-zero on failure.
- Preserve region isolation semantics in fetch logic (one region failure should not stop others).

## Data and Output Rules
- Canonical records must satisfy `schema.REQUIRED_FIELDS` and `SCHEMA_VERSION`.
- Keep deterministic ordering by `(region, rank, video_id)`.
- JSON writing conventions:
  - `sort_keys=True`
  - compact separators `(',', ':')`
  - `ensure_ascii=False`
  - UTF-8 encoding
- Keep JSONL and manifest newline-terminated.

## Testing Conventions
- Use pytest function-style tests.
- Use `pytest.mark.parametrize` for boundary/matrix coverage.
- Use `pytest.raises(..., match=...)` or exact-string error assertions.
- Use fakes/monkeypatch to avoid live network dependencies.
- Keep tests deterministic and fixture-driven.

## Static Analysis Notes
- Some tests intentionally include `# pyright: reportMissingImports=false`.
- Do not remove these pragmas unless import resolution strategy is updated.

## Common Pitfalls
- Forgetting `PYTHONPATH=src` for `python -m phase1_youtube...` commands.
- Changing stable error text and breaking assertion-based tests.
- Introducing non-deterministic sort/serialization behavior.
- Refactoring broadly when only a minimal bugfix is needed.

## Recommended Verification Before Finalizing Changes
Always run:

```bash
pytest -q
```

For pipeline-related changes, also run:

```bash
PYTHONPATH=src python -m phase1_youtube.ingest --regions JP,US --top-n 2 --offline-fixtures tests/fixtures --out output/agent-check.jsonl
PYTHONPATH=src python -m phase1_youtube.validate_output --input output/agent-check.jsonl
```

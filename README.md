# CONSORT RCT Checklist Evaluator

A browser and command-line checklist for reviewing randomized-trial reports against **CONSORT 2025**. The current standard contains 30 numbered items; this repository represents them as 42 scored entries where the checklist contains lettered sub-items.

## What it does

- Records each reporting item as **Full**, **Partial**, **No**, or **N/A**.
- Calculates a repository-defined completion percentage and section summaries.
- Lists incomplete reporting items for follow-up.
- Optionally checks participant-flow counts for arithmetic inconsistencies.
- Supports single-trial CLI evaluation and CSV batch processing.
- Provides a static browser interface with light and dark themes and JSON/CSV export.

The completion percentage is **not an official CONSORT score**, a trial-quality rating, or a Cochrane RoB 2 judgement. RoB 2 requires its own result-specific signalling questions and decision algorithm.

## Browser use

The web application runs entirely in the browser with HTML, CSS, and JavaScript. Checklist data are not uploaded by the application. The only browser preference stored locally is the selected light/dark theme.

## CLI use

Requires Python 3.9 or later and has no runtime third-party dependencies.

```bash
python cli.py --full-compliance
python cli.py --responses-json '{"1a":"FULL","1b":"PARTIAL","2":"FULL"}'
python cli.py --interactive
python cli.py batch -i sample.csv -o results.csv
python cli.py batch -i sample.csv -o results.json --json
```

Accepted checklist values are `FULL`, `PARTIAL`, `NO`, and `NA` (case-insensitive; common short forms are also accepted). Missing values are treated as not reported. Invalid non-empty values are rejected.

## Testing

```bash
python -m pip install pytest
python -m pytest -q
python -m compileall -q cli.py consort_evaluator.py tests
node --check site/app.js
```

GitHub Actions tests Python 3.9–3.13, exercises the CLI batch workflow, validates browser JavaScript syntax, and builds the Python package.

## Methodological basis

The checklist is based on the CONSORT 2025 statement:

- Hopewell S, et al. *CONSORT 2025 statement: updated guideline for reporting randomised trials.* BMJ. 2025;389:e081123. doi:10.1136/bmj-2024-081123.
- CONSORT–SPIRIT: https://www.consort-spirit.org/
- Cochrane RoB 2 guidance: https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-08

CONSORT 2025 supersedes CONSORT 2010. The participant-flow checker verifies reported arithmetic only; it does not infer intention-to-treat adherence or risk of bias.

## Browser compatibility

The static application uses standard modern HTML, CSS, and JavaScript and is intended for current desktop and mobile versions of Chrome, Edge, Firefox, and Safari. No server-side Python runtime is required.

## License

MIT. See [LICENSE](LICENSE).

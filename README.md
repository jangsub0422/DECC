# DECC

DECC is an AI-assisted code generation pipeline that decomposes a natural-language program request into structured module blueprints, generates Python modules in batch, validates them, and links them into a runnable application.

Current release status: `0.0.1-alpha`

## What DECC Does

- Accepts a natural-language specification
- Uses an architect step to split the request into multiple `plasmid_*.json` module blueprints
- Generates Python modules from those blueprints
- Validates syntax and profile-based contracts
- Integrates valid outputs into a runnable `final_app.py`

## Current Scope

DECC currently includes profile-aware normalization for:

- `cli_crud`
- `file_transformer`
- `data_analysis`

This is still an alpha release. Generated code may be incomplete, inconsistent, or unsuitable for production use without review.

## Disclaimer

This project uses AI-assisted generation in multiple stages, including decomposition, code generation, validation feedback, and integration guidance.

- Outputs may contain bugs, omissions, security issues, or incorrect assumptions.
- The generated results are not guaranteed to be correct, complete, or production-ready.
- Human review and testing are strongly recommended before real use.
- Extra caution is required for security-sensitive, legal, medical, financial, or privacy-sensitive workflows.

## Project Structure

```text
architect.py
-> plasmids_batch/runs/<run_name>/plasmid_*.json
-> run_batch.py
-> outputs/runs/<run_name>/*.py
-> integration.py
-> outputs/runs/<run_name>/final_app.py
-> root final_app.py
```

Important directories:

- `plasmids_batch/runs/`: generated blueprint runs
- `outputs/runs/`: generated Python runs
- `code_pipeline/`: contracts, assay, protocol, run-path helpers
- `web_app.py`: Streamlit wrapper UI

## Requirements

- Python 3.11+ recommended
- Optional API key depending on architect host
- Ollama only if using the local architect/code-generation path

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running With The Web Wrapper

Quick launchers:

```text
Windows: start_decc_windows.bat
Linux:   start_decc_linux.sh
```

You can also run Streamlit directly:

```bash
streamlit run web_app.py
```

Recommended flow:

1. Enter a program specification
2. Enter a run name / project name
3. Choose the architect host and model
4. Generate plasmids
5. Review the current plasmids
6. Run batch generation
7. Run integration
8. Test `final_app.py`

## Running From The CLI

Generate plasmids through `architect.py`, then run:

```bash
python run_batch.py
python integration.py
python final_app.py
```

If your environment uses a different launcher, use that launcher instead of `python`.

## Versioning

This repository currently targets:

- `0.0.1-alpha`: first public alpha milestone

Version metadata is stored in:

- `VERSION.txt`
- `code_pipeline/__init__.py`

## Included Documentation

- `USER_GUIDE_KO.txt`
- `USER_GUIDE_EN.txt`

## Known Alpha Limitations

- Generated modules may still fail contract checks
- Entry modules may still require prompt tuning for some use cases
- Profile coverage is limited
- End-to-end output quality depends heavily on the selected model
- The pipeline is designed for experimentation, not guaranteed production delivery

## Suggested First GitHub Release Notes

Use `CHANGELOG.md` and `RELEASE_NOTES_0.0.1-alpha.md` as the initial release summary.

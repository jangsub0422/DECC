# DECC 0.0.2-alpha

DECC `0.0.2-alpha` is the second public alpha release of the Digital E. coli Code Compiler project.

This release focuses on making the early pipeline easier to operate and easier to diagnose. It improves model selection, run-level reporting, and integration-time checks without changing the basic workflow.

## Highlights

- Added provider model discovery for Gemini, OpenAI, and Claude.
- Kept fallback model lists so the wrapper still works when provider lookup fails.
- Updated hosted model defaults and API quickstart examples.
- Added run-level `batch_report.json` and `batch_report.md` outputs.
- Added import smoke checks before linking `final_app.py`.
- Prevented run-local `final_app.py` snapshots from being scanned as generated modules.
- Added dependency version ranges in `requirements.txt`.
- Clarified the full project name: Digital E. coli Code Compiler.
- Added English API quickstart documentation.

## Current Runtime Positioning

- Recommended default: local-first workflow with Python, Streamlit, and Ollama.
- Hosted APIs are available for architect decomposition and module code generation.
- Hosted API usage remains optional and may introduce cost or provider-specific variability.

## Important Notes

- This is still an alpha release.
- Generated code must be reviewed carefully before execution, reuse, redistribution, or deployment.
- Import smoke checks catch some runtime issues, but they do not prove that the generated application behaves correctly.
- Profile-specific runtime schema tests are not complete yet.

## Upgrade Notes

- Install dependencies again if your environment was created before this release.
- Existing `0.0.1-alpha` run folders can remain in place.
- New batch runs will include `batch_report.json` and `batch_report.md` in the active output run directory.

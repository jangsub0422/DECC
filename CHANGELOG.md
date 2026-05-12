# Changelog

## 0.0.2-alpha - 2026-05-12

Second public alpha release of DECC.

- Added provider model discovery with fallback model lists for Gemini, OpenAI, and Claude
- Updated hosted model defaults and API quickstart examples
- Added request refinement metadata to generated plasmids
- Added run-level batch reports in JSON and Markdown formats
- Added import smoke checks before integration links `final_app.py`
- Excluded run-local `final_app.py` snapshots from generated module scans
- Added dependency version ranges to `requirements.txt`
- Clarified the project name as Digital E. coli Code Compiler
- Added English API quickstart documentation

Known limitations:

- Import smoke checks do not yet execute full interactive workflows
- Profile-specific runtime schema tests are still future work
- Hosted provider model availability can still vary by account, region, or API policy

## 0.0.1-alpha - 2026-05-07

First public alpha release of DECC.

- Added profile-aware architect normalization
- Added run-based plasmid storage
- Added run-based output storage
- Added profile-aware contracts and assay checks
- Added integration linker improvements with active-run output loading
- Promoted `integration.py` to the stable entry point and kept versioned wrappers for compatibility
- Added Streamlit wrapper for multiline input and run management
- Added Korean and English user guides
- Added user-facing disclaimers and review notices

Known limitations:

- Output quality still depends strongly on the chosen model
- Some prompts may still need tightening for stricter module separation
- End-to-end runs should be manually reviewed and tested

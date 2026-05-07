# DECC 0.0.1-alpha

DECC `0.0.1-alpha` is the first public alpha milestone for the project's AI-assisted software generation pipeline.

## Highlights

- Natural-language request decomposition into plasmid JSON blueprints
- Profile-aware normalization for common app structures
- Batch module generation and validation
- Run-based storage for plasmids and generated outputs
- Integration linker (`integration.py`) that builds a runnable `final_app.py`
- Streamlit wrapper for multiline input and run management

## Recommended Positioning

This release is best presented as:

- an experimental alpha
- a structured prototype
- a local-first AI software pipeline

It should not yet be presented as a production-ready generator.

## Suggested GitHub Release Summary

DECC 0.0.1-alpha introduces the first public alpha of a structured AI-assisted code generation pipeline. This release includes architect-driven blueprint generation, profile-aware normalization, run-based artifact storage, contract-aware validation, integration linking, and a Streamlit wrapper for easier interactive use.

## Release Cautions

- Generated outputs still require manual review
- Some profiles and prompts remain under active tuning
- API/model behavior may affect decomposition and generation quality
- Hosted API support for module code generation is still in progress
- End-to-end reliability is improving, but not finalized

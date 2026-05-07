# Changelog

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

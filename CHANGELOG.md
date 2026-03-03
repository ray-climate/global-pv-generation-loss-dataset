# Changelog

All notable changes to this repository are documented in this file.

## [1.0.0] - 2026-03-03

### Added
- Publication-ready figure replication script for global aerosol loss vs new PV generation:
  - `scripts/examples/plot_aerosol_loss_vs_new_generation.py`
- Publication-ready 2023 country-level manuscript Fig.2f replication script:
  - `scripts/examples/plot_country_aerosol_loss_2023.py`
- Parquet interpretation script:
  - `scripts/examples/interpret_global_pv_parquet.py`
- Citation metadata file:
  - `CITATION.cff`
- Code license:
  - `LICENSE` (MIT)
- CI smoke test workflow:
  - `.github/workflows/ci.yml`

### Changed
- README rewritten with Zenodo-style overview, data source guidance, citation instructions, and sanity-check outputs.
- Dependency versions pinned in `requirements.txt`.
- Plot font configuration updated to include safe cross-platform fallbacks.

### Notes
- The authoritative research dataset is hosted on Zenodo:
  - https://zenodo.org/records/18794231

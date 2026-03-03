# Release Checklist (CSV-only repo)

## Data
- [ ] Confirm all intended CSV files are present in `data/`.
- [ ] Confirm no non-CSV heavy files are committed (e.g., GPKG, Parquet).
- [ ] Verify row counts and key columns match Zenodo release records.

## Metadata
- [ ] Update `metadata/zenodo_metadata_draft.json` to final version.
- [ ] Regenerate `metadata/CHECKSUMS.sha256` after any CSV change.

## Reproducibility
- [ ] Run example scripts in `scripts/examples/` successfully.
- [ ] Confirm outputs regenerate in `outputs/tables/` and `outputs/figures/`.

## Final QA
- [ ] Ensure `.DS_Store` and temporary files are absent.
- [ ] Tag release version (e.g., `v1.0.0`).

# Sprint 1 Retrospective

## What Went Well

- Excel header normalization handles both title-row and direct-header workbook formats.
- SQLite rebuilds are repeatable through the Makefile `load` and `report` targets.
- Critical data-quality failures are separated from warning-level source-data issues.

## What Changed

- All 12 provided Excel files are now represented in `nifty100.db` and `output/load_audit.csv`.
- Rows outside the 92-company master are rejected before insert as non-critical warning rejections to preserve FK integrity.

## Follow-Ups

- Confirm with the mentor whether Sprint 2 should keep all 12 normalized tables or collapse supplementary sources into derived marts.
- Build dashboard/API targets in Sprint 2 using the existing Makefile placeholders.

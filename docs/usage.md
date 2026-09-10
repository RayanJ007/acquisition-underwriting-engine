# Model usage

Start with the environment and run commands in the [README](../README.md). `python -m src.pipeline` rebuilds CSV tables, chart PNGs, `outputs/model.json` and the investment memo from local snapshots. It overwrites those generated artifacts but does not update the workbook. Run experiments on a copy or inspect your diff before keeping changed outputs.

## Excel

Open [acquisition_model.xlsx](../models/acquisition_model.xlsx) without macros.

- **Assumptions D6:** choose 1 (base), 2 (upside) or 3 (downside). Each driver has editable annual case inputs.
- **LBO D6:** edit entry enterprise value in USD millions.
- **DCF D28:** choose 1 for Gordon growth or 2 for the exit-multiple method.
- **Goal Seek:** set LBO D45 to 0.20 by changing LBO D6 to explore the base hurdle price, then inspect downside separately.

Keep workbook assumptions aligned with [Python configuration](../config/assumptions.yaml) when comparing results. Excel's selected-case label checks that case's hurdle and funding, then says “Proceed to downside diligence” if it passes. Python's final rule also requires a nonnegative downside return. The [validation record](validation.md) distinguishes formula/cached-value checks from native Excel UI testing.

## Streamlit

Run `python -m streamlit run dashboard/app.py` from the repository root. The interface provides operating, debt/returns, sensitivity and statement/check views, plus a scenario CSV download.

The scenario dropdown supplies operating assumptions; explicit controls then override some inputs. For example, selecting downside while leaving interest at 7.5% and exit at 14x does not reproduce the saved downside's 9.5% and 10x. A separate downside stress adds 2 percentage points to the interest control and subtracts 4x from the exit control.

The margin control is a baseline: a 28% selection yields effective margins of 30% in upside and 24% in downside. The caption reports the effective margin. Default dashboard WACC is rounded to 8.95%, compared with the pipeline's 8.946%. Match effective inputs before comparing outputs. Python supports one to ten forecast years; the workbook is a five-year layout.

## Source refresh

See [data sources and provenance](../data/README.md) for snapshot refresh commands and source-selection conventions. Downloads require an identifying `SEC_USER_AGENT` for SEC requests; reproducing the committed case does not require a download or API key.

## Manual historical import and target adaptation

The manual path accepts the same columns as [historicals.csv](../data/processed/historicals.csv), with an adjacent `provenance.csv` containing at least `field`, `period_end`, `source`, `units` and `currency`. Use disclosed amounts and consistent units. The importer validates the required schema and selected financial relationships; a ledger header alone does not establish complete source support.

```powershell
python -m src.pipeline --manual path/to/historicals.csv
```

For a different target:

1. Update [company configuration](../config/company.yaml), segment starting sales, peer identities and dates, then review [financial assumptions](../config/assumptions.yaml).
2. Supply normalized target history and its provenance. Automatic historical tag mappings and zero-debt treatment apply only to Garmin.
3. Supply raw SEC and market snapshots needed for share counts and peers. Review issuer-specific debt/share tags rather than assuming equivalent definitions.
4. Adapt Garmin-specific presentation labels and the workbook layout. Python accepts a variable number of revenue segments, but changing YAML does not rewrite Excel.
5. Review currency handling explicitly: changing the currency label does not translate the USD-based extraction or valuation.
6. Rerun tests and reconcile source, operating, valuation and financing outputs before using the new case.

This is an adaptation workflow, not a universal ticker-switching service.

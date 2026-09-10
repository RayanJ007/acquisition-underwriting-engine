# Validation record

Validated on 2026-09-06 in a fresh Python 3.13 virtual environment using the dependency versions recorded in requirements.lock.txt.

| Check | Result |
|---|---|
| Dependency installation and pip check | Clean installation; no broken requirements |
| Full Python test suite | 28 passed |
| Offline pipeline | Historical data, three scenarios, DCF, peers, QoE, LBO, sensitivities, charts and memo generated |
| Historical source selection | Five exact annual fiscal periods; facts filed after the cutoff rejected |
| Cash-flow completeness | Custom acquisition and cash repurchase-plan tags verified against original 10-K tables |
| Statement integrity | Cash, debt, equity, PP&E and balance-sheet residuals below 1e-7 million |
| Target-IRR solver | Recomputed sponsor IRR equals the 20% hurdle within 1e-8 |
| Loss and financing-shortfall case | No immediate loss tax refund; explicit borrowing; statements remain balanced |
| Streamlit interaction | Growth changes update returns; invalid WACC/growth combination displays an error |
| Actual Streamlit server | HTTP 200 on /_stcore/health; smoke process stopped after check |
| Review notebooks | All three executed; production-module cells also exercised by tests |
| Excel formula parity | Base/upside/downside revenue, EV, IRR and exit debt match Python within 1e-6 |
| Excel sensitivity/input propagation | Later-period driver changes affect that and later periods; earlier periods unchanged |
| Excel formula errors | No matched formula errors |
| Saved XLSX | Sixteen sheets; cached EV/IRR reconcile to JSON; no error cells or external-workbook links; live chart part present |
| Visual QA | All sixteen sheets rendered and inspected; labels, formats, heatmaps and chart reviewed |

The recorded workbook checks are in [workbook_validation.json](../outputs/workbook_validation.json). Native Microsoft Excel UI verification was unavailable; no claim is made about native print pagination or rendering. The workbook uses standard formulas and does not depend on macros.

Reproduction commands are in the [README](../README.md). The Python outputs are deterministic for a fixed data/configuration snapshot; binary workbook IDs, package-dependent chart rendering, and metadata can change without changing financial results. Original raw data is fingerprinted in data/raw/manifest.json.

## Portfolio polish verification — September 10, 2026

- The existing virtual environment satisfied every pinned requirement with an offline install check.
- The main pipeline completed and reproduced the same financial conclusions; all 28 tests passed.
- The local Streamlit server returned HTTP 200 in the existing smoke check.
- Relative Markdown file links resolved, and the two README previews use inspected, existing PNG outputs with repository-relative paths. No UI screenshots were created.
- README scenario figures matched the generated results. Source code, tests, configuration, raw/processed financial data, workbook and saved analytical outputs retained their pre-edit fingerprints.
- Git attributes mark only `data/raw/*.html` as vendored. Excel owner files, local environment files and notebook checkpoints are ignored. The temporary Excel owner file was removed from tracking while retained locally.

This pass did not repeat native Excel UI validation or verify a remote GitHub Actions run. The historical advertising/SG&A classification gap remains documented in the [data dictionary](data_dictionary.md#historical-expense-classification); it was not changed during presentation cleanup.

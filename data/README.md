# Data sources and provenance

The committed snapshots reproduce a historical case with a **February 28, 2025** information cutoff. Source retrieval timestamps are recorded separately. Financial amounts are normalized to USD millions.

## What is stored

| Files | Purpose |
|---|---|
| `raw/*_companyfacts.json` | Original SEC Company Facts responses for Garmin, Logitech and Polaris. |
| `raw/*_market.json` | Yahoo daily chart responses; the model selects the dated unadjusted close, not current metadata. |
| `raw/GRMN_*_10K.html` | Original Garmin annual reports used for custom inline-XBRL disclosures. |
| `raw/*.source.json` | Source URLs and retrieval timestamps; reconstructed timestamps are labeled. |
| `raw/custom_cash_flows.json` | Acquisition and repurchase-plan cash payments extracted from the reports. |
| `raw/manifest.json` | SHA-256 fingerprints and byte counts for source files. |
| `processed/historicals.csv` | Normalized FY2020–FY2024 Garmin financials. |
| `processed/provenance.csv` | Selected historical tags, periods, accessions, filing dates and sources. |
| `processed/peer_provenance.csv` | Source records for peer financial inputs. |

Raw SEC filing HTML is retained for disclosures that require direct inline-XBRL extraction. [The extraction script](../scripts/extract_custom_facts.py) uses Beautiful Soup to read financial tags and their period contexts, rather than screen positions or visual table layouts. It selects consolidated annual contexts for acquisition and repurchase cash payments. The 2020/2021 repurchase-plan zeros reflect explicit dashes in the FY2022 cash-flow table, not missing-data defaults.

## Selection and accounting conventions

[The data module](../src/data.py) matches exact fiscal period ends, accepts annual flows of 350–380 days and excludes filings after the cutoff. Garmin uses a 52/53-week calendar. Later eligible comparatives take precedence within the selected tag; this is an as-of case rather than an original-filing-vintage study.

Operating D&A includes depreciation and intangible amortization, excluding securities amortization. EBITDA is derived from reported components. Outflow inputs such as CapEx use positive magnitudes; aggregate CFI, CFF and FX movements retain their signs. Buybacks combine repurchase-plan cash payments and employee share withholding, rather than using an accrual-based equity-statement repurchase measure.

Garmin's zero financial debt is an explicit disclosure-based convention, not a generic missing-data fallback. Operating leases remain in other assets/liabilities and rental expenses. Residual asset/liability buckets preserve accounts not modeled separately. See the [data dictionary](../docs/data_dictionary.md) for definitions and the known FY2020/2021 advertising/SG&A classification limitation.

FY2024 segment sales and the source-release URL are in [company configuration](../config/company.yaml). Source thousands are converted to millions. Fiscal-end shares approximate shares on the market date. Peers retain their individual fiscal ends and are historical annual references, not LTM or forward comparables.

## Reproduce or refresh

The normal pipeline uses the committed snapshots without network access. To replace API snapshots, set `SEC_USER_AGENT` to your real identifying research contact, then run from the repository root:

```powershell
python scripts/download_data.py --refresh
python scripts/extract_custom_facts.py
python -m src.pipeline
```

Use your environment's Python executable. Without `--refresh`, the downloader preserves existing API files. The extraction script reuses existing annual-report HTML and downloads it only if missing. Network failures raise errors rather than creating substitute financial figures. Refresh does not change the configured information cutoff. Preserve the original snapshots when reproducing the published case.

For manual imports or a different target, follow [model usage](../docs/usage.md). The automatic historical mappings and zero-debt convention are Garmin-specific.

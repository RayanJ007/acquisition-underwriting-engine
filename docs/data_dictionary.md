# Data dictionary

All monetary fields use USD millions. Period labels are fiscal, not calendar approximations. Monetary outflow magnitudes are positive except signed CFO/CFI/CFF/FX and net changes. Undefined ratios remain missing, not zero.

| Field | Definition / source |
|---|---|
| `year` | Fiscal year label |
| `period_end` | Actual fiscal closing date |
| `revenue` | SEC US-GAAP tag: RevenueFromContractWithCustomerExcludingAssessedTax, SalesRevenueNet |
| `cogs` | SEC US-GAAP tag: CostOfGoodsAndServicesSold, CostOfRevenue |
| `gross_profit` | SEC US-GAAP tag: GrossProfit |
| `ebit` | SEC US-GAAP tag: OperatingIncomeLoss |
| `sga` | SEC US-GAAP tag: SellingGeneralAndAdministrativeExpense; advertising classification changes across the historical series (see below). |
| `rd` | SEC US-GAAP tag: ResearchAndDevelopmentExpense |
| `depreciation` | SEC US-GAAP tag: Depreciation |
| `amortization` | SEC US-GAAP tag: AmortizationOfIntangibleAssets |
| `taxes` | SEC US-GAAP tag: IncomeTaxExpenseBenefit |
| `net_income` | SEC US-GAAP tag: NetIncomeLoss |
| `cash` | SEC US-GAAP tag: CashAndCashEquivalentsAtCarryingValue |
| `ar` | SEC US-GAAP tag: AccountsReceivableNetCurrent |
| `inventory` | SEC US-GAAP tag: InventoryNet |
| `other_current_assets` | SEC US-GAAP tag: PrepaidExpenseAndOtherAssetsCurrent |
| `ppe` | SEC US-GAAP tag: PropertyPlantAndEquipmentNet |
| `intangibles` | SEC US-GAAP tag: OtherIntangibleAssetsNet |
| `goodwill` | SEC US-GAAP tag: Goodwill |
| `ap` | SEC US-GAAP tag: AccountsPayableCurrent |
| `accrued` | SEC US-GAAP tag: OtherAccruedLiabilitiesCurrent |
| `current_liabilities` | SEC US-GAAP tag: LiabilitiesCurrent |
| `assets` | SEC US-GAAP tag: Assets |
| `equity` | SEC US-GAAP tag: StockholdersEquity |
| `investments` | SEC US-GAAP tag: AvailableForSaleSecuritiesDebtSecurities |
| `cfo` | SEC US-GAAP tag: NetCashProvidedByUsedInOperatingActivities |
| `capex` | SEC US-GAAP tag: PaymentsToAcquirePropertyPlantAndEquipment |
| `cfi` | SEC US-GAAP tag: NetCashProvidedByUsedInInvestingActivities |
| `cff` | SEC US-GAAP tag: NetCashProvidedByUsedInFinancingActivities |
| `dividends` | SEC US-GAAP tag: PaymentsOfDividends |
| `employee_share_withholding` | SEC US-GAAP tag: TreasuryStockValueAcquiredCostMethod |
| `sbc` | SEC US-GAAP tag: ShareBasedCompensation |
| `restricted_cash_total` | SEC US-GAAP tag: CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents |
| `cash_change` | SEC US-GAAP tag: CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect |
| `fx_cash` | SEC US-GAAP tag: EffectOfExchangeRateOnCashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsIncludingDisposalGroupAndDiscontinuedOperations |
| `acquisitions` | Cash acquisition consideration net of cash acquired; custom inline-XBRL cash-flow tag |
| `repurchase_plan` | Cash paid under the share repurchase plan, including settlement timing |
| `buybacks` | Employee share withholding plus share repurchase-plan cash payments |
| `debt` | Financial borrowings; disclosed zero for Garmin |
| `interest` | Financial-debt interest expense; zero for debt-free Garmin |
| `debt_issuance` | New financial borrowings; zero in case history |
| `debt_repayment` | Financial debt repayments; zero in case history |
| `da` | Depreciation plus operating intangible amortization |
| `ebitda` | Reported operating income plus operating D&A |
| `other_assets` | Total assets less explicitly modelled assets; includes tax/lease and other disclosed accounts |
| `other_current_liabilities` | Current liabilities less AP and selected accruals; held fixed in forecast |
| `other_liabilities` | Total assets less equity, current liabilities and financial debt |

## Historical expense classification

The normalized FY2020/2021 SG&A values exclude separately disclosed advertising of $151.166m and $171.829m. From FY2022, the selected SG&A values include advertising. Add the earlier advertising expenses when reconciling gross profit less operating costs to EBIT; do not interpret this column as a consistent five-year expense series. The amounts appear in the saved FY2022 10-K income statement. Reported EBIT and derived EBITDA are sourced independently and remain intact. The existing tests do not check this operating-expense bridge.

## Forecast fields

Segment revenue grows by the respective segment driver plus scenario shift. Cash COGS, R&D and SG&A use revenue ratios. `nwc = ar + inventory + other_current_assets - ap - accrued`; `change_nwc` compares consecutive periods. `fcff = EBIT - cash tax on positive EBIT + D&A - CapEx - change_nwc`. Losses do not generate immediate tax refunds. `cfo = net_income + D&A - change_nwc`. The `check_*` columns are monetary residuals with tolerance 1e-7 million.

## Ratios

ROA and ROE use average beginning/ending assets/equity; the first year is unavailable. ROIC uses reported effective tax and average equity + debt - cash - securities. Working-capital days use closing balances and 365 days. Interest coverage with zero interest is unavailable. EBITDA is a derived operating metric, not cash flow. Net debt includes liquid securities and can be negative.

## Market and peer fields

`price` is a dated unadjusted close in USD/share; `shares` is fiscal-end shares in millions. Logitech shares equal issued less treasury shares. `market_cap = price * shares`; `enterprise_value = market_cap + debt - cash` for peers. Target net debt also subtracts marketable securities. Nonpositive peer earnings denominators yield unavailable multiples and are omitted from statistics. Peer labels explicitly say Historical FY.

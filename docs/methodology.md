# Financial methodology and assumptions

This is a historical underwriting case with a 2025-02-28 information and market cutoff. FY2025–FY2029 forecasts are analyst assumptions, not observed results. Annual year-end cash-flow discounting treats the latest fiscal balance sheet as time zero, approximating the two-month gap to the market observation. No 2025 operating actuals are used.

## Forecast

Five Garmin segments grow independently. Base growth of 9% Fitness, 6% Outdoor, 5% Aviation, 6% Marine and 15% Auto OEM moderates FY2024's 20% group growth. Upside adds 3 percentage points to each driver; downside subtracts 6. These are illustrative underwriting judgments, not management guidance. No unit data is fabricated.

COGS 41.3%, R&D 15.8% and cash SG&A 14.9% of revenue target 28% EBITDA margin. The forecast shows D&A separately and uses approximate cash-cost ratios. It does not reconstruct the disclosed allocation of D&A across functional expenses. Upside/downside changes cash SG&A by -2/+4 revenue percentage points. FY2024's derived EBITDA includes depreciation plus intangible amortization, avoiding non-operating securities amortization.

AR uses DSO, inventory uses DIO and AP uses DPO on 365 days. Historical days also use closing balances/365 to make the driver comparison consistent, even in 53-week years. Base DSO 57, DIO 200 and DPO 50 approximately track the latest reported balances. Other operating current assets 5.6% and accrued liabilities 3.4% scale with sales. Other current liabilities (including taxes and dividend payables), goodwill, securities, other assets and other liabilities stay fixed. These fixed balances need review in a transaction case.

CapEx is 3.5% of revenue (4.5% downside), above FY2024's 3.1%, to fund growth. Depreciation uses 11% of beginning net PP&E plus half-year CapEx; intangible amortization is $30.666m annually, capped at the remaining balance. PP&E and intangible balances roll forward independently. No acquisitions, new goodwill, OCI, FX, asset sales or further securities investment is projected. Existing securities are held at book value. SBC is treated as a recurring economic cash cost, with no addback or dilution forecast.

Standalone dividends equal 40% of positive net income. Debt interest uses opening balances. Mandatory repayments are 1% of original debt; excess cash above $300m repays remaining debt. A shortfall produces a modeled funding draw; facility availability is not established. There is no circularity and no balance-sheet plug. Equity rolls through net income and dividends. Forecast current/deferred taxes are simplified to cash taxes on positive pretax income; there is no NOL carryforward model.

## Valuation assumptions

Illustrative nominal USD WACC inputs: risk-free 4.3%, beta 1.0, equity risk premium 5.5%, debt cost 7%, target debt weight 20%, tax 21%. These are explicit analyst assumptions, not sourced observations. Terminal growth 2.5%; Gordon valuation requires WACC above growth. Existing cash and marketable securities are added and financial debt subtracted once. Lease liabilities are excluded consistently with rental costs in operating earnings. Acquisition minimum cash is separately funded at closing.

## Interpretation

This is simplified public-information diligence. Customer retention, channel inventory, supplier concentration, warranty reserves, tax restructuring, pension exposure and change-of-control costs need primary diligence. A debt-free target with substantial financial assets can still be an unattractive leveraged acquisition at an excessive entry multiple.

## Acquisition mechanics

Entry EV defaults to 15x FY2024 EBITDA. Debt is the lower of 3x EBITDA and 70% of EV, preventing negative sponsor equity at low trial prices. Fees are 2% of EV plus 2% of new debt. Existing cash and securities increase the equity purchase consideration and are simultaneously a closing source; their effects cancel in sponsor equity. Existing debt is refinanced. $300m is newly retained for operations. This avoids counting financial assets twice and explicitly assumes all securities can be realized at book value without tax or transaction leakage.

No interim sponsor distributions are paid. After cash taxes, CapEx, working-capital changes and opening-debt interest, all available cash above the minimum sweeps debt. Cash accumulates after debt is repaid. A shortfall draws an explicit additional facility at the same interest rate; the dashboard flags required funding. Unlimited facility availability is a modelling diagnostic, not a financing commitment. Exit equity is EV less remaining debt plus retained cash, floored at zero. With one initial equity outflow and one terminal receipt, IRR equals MOIC^(1/years)-1 exactly. Bisection solves maximum entry EV for the 20% hurdle. Exit EBITDA multiples are 14x base, 16x upside, and 10x downside; these are scenario assumptions, not peer-derived facts.

QoE retains recurring R&D and SBC as economic costs. No non-recurring EBITDA addbacks are applied without evidence. Non-operating FX and tax items can explain net-income volatility but are already outside EBITDA, so adding them again would be incorrect. QoE scenario adjustments supported by the API are shown in the bridge only; investment cases use reported-derived EBITDA unless the analyst explicitly changes transaction/forecast assumptions.

Terminal FCFF grows the final forecast cash flow at the selected perpetual rate; a separate terminal ROIC/reinvestment model is not included. Loss years receive no immediate tax refunds. In the forecast and Excel DCF, NOPAT equals EBIT less tax on positive EBIT.

## Limits that affect interpretation

The assumed $26.48bn entry EV is below the saved public-market EV of $40.36bn before any takeover premium. The modeled price does not establish seller acceptance. The maximum-price solver targets the selected case's IRR; it does not impose downside protection or lender constraints.

DCF adds all existing cash and securities to enterprise value without independently reserving operating cash. The acquisition separately funds a $300m minimum. Cash restrictions, liquidity needs and tax leakage require review before applying either value to a transaction.

The two historical peers differ in business mix and fiscal dates. The model does not include synergies, purchase accounting, detailed tax rules, exit fees or lender covenants. The historical expense series also has an [advertising/SG&A classification gap](data_dictionary.md#historical-expense-classification); reported EBIT and EBITDA remain intact.

The final Python recommendation requires no additional base/downside funding, base IRR at least the target, and downside IRR at least zero. DCF, comps and QoE support the memo but do not directly enter that rule. See [usage](usage.md) for the workbook's preliminary decision and dashboard override behavior.

"""Non-circular debt waterfall with explicit liquidity borrowing."""


def debt_schedule(
    opening: float,
    cash_before_financing: float,
    minimum_cash: float,
    rate: float,
    original_debt: float,
    amortization: float,
    sweep: float = 1.0,
) -> dict:
    if (
        min(opening, minimum_cash, rate, original_debt, amortization) < 0
        or not 0 <= sweep <= 1
    ):
        raise ValueError("Invalid debt assumptions")
    mandatory = min(opening, original_debt * amortization)
    borrowing = max(0.0, minimum_cash - cash_before_financing + mandatory)
    optional = min(
        max(0.0, opening - mandatory),
        max(0.0, cash_before_financing - mandatory - minimum_cash) * sweep,
    )
    closing = opening + borrowing - mandatory - optional
    return dict(
        opening_debt=opening,
        borrowing=borrowing,
        mandatory_repayment=mandatory,
        optional_repayment=optional,
        interest=opening * rate,
        debt=closing,
        cash=cash_before_financing + borrowing - mandatory - optional,
    )

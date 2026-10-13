"""Cash and inventory accounting for executed trades.

All money is stored as integer pence. Short positions and borrowing cash are
allowed without financing costs. Trading fees and optional closing costs are
supported, and both default to zero.
"""


def require_integer(value: int, name: str, minimum: int | None = None) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")


class Account:
    """An account starting with cash and no inventory."""

    def __init__(self, starting_cash_pence: int = 100_000, fee_pence_per_share: int = 0):
        require_integer(starting_cash_pence, "starting cash", minimum=0)
        require_integer(fee_pence_per_share, "fee per share", minimum=0)
        self.starting_cash_pence = starting_cash_pence
        self.cash_pence = starting_cash_pence
        self.inventory = 0
        self.fee_pence_per_share = fee_pence_per_share
        self.total_fees_pence = 0

    def buy(self, quantity: int, price_pence: int) -> None:
        """Record a fill in which we BUY shares, typically at our bid."""
        require_integer(quantity, "quantity", minimum=1)
        require_integer(price_pence, "price", minimum=1)
        fee = quantity * self.fee_pence_per_share
        self.cash_pence -= quantity * price_pence + fee
        self.total_fees_pence += fee
        self.inventory += quantity

    def sell(self, quantity: int, price_pence: int) -> None:
        """Record a fill in which we SELL shares, typically at our ask."""
        require_integer(quantity, "quantity", minimum=1)
        require_integer(price_pence, "price", minimum=1)
        fee = quantity * self.fee_pence_per_share
        self.cash_pence += quantity * price_pence - fee
        self.total_fees_pence += fee
        self.inventory -= quantity

    def close_position(self, reference_price_pence: int, exit_cost_pence_per_share: int = 0) -> dict:
        """Close at reference minus cost when long, plus cost when short.

        This assumed external execution is not a fill on our own quotes.
        The same per-share trading fee applies to the closing trade. Constant
        execution cost and unlimited available exit quantity are simplifications.
        """
        require_integer(reference_price_pence, "reference price", minimum=1)
        require_integer(exit_cost_pence_per_share, "exit cost", minimum=0)
        quantity = abs(self.inventory)
        execution_price = None
        if self.inventory > 0:
            execution_price = reference_price_pence - exit_cost_pence_per_share
            self.sell(quantity, execution_price)
        elif self.inventory < 0:
            execution_price = reference_price_pence + exit_cost_pence_per_share
            self.buy(quantity, execution_price)
        return {
            "quantity": quantity,
            "execution_price": execution_price,
            "execution_cost": quantity * exit_cost_pence_per_share,
            "closing_fee": quantity * self.fee_pence_per_share,
            "final_pnl": self.pnl_pence(reference_price_pence),
        }

    def equity_pence(self, reference_price_pence: int) -> int:
        """Value cash and remaining inventory at the reference price."""
        require_integer(reference_price_pence, "reference price", minimum=1)
        return self.cash_pence + self.inventory * reference_price_pence

    def pnl_pence(self, reference_price_pence: int) -> int:
        return self.equity_pence(reference_price_pence) - self.starting_cash_pence


def pounds(pence: int) -> str:
    return f"£{pence / 100:,.2f}"

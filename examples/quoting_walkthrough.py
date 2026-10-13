"""Connect quotes, customers, fills, price changes and the account ledger."""

import random

from mmsim.customers import execute_customer, fixed_quotes, generate_customer
from mmsim.ledger import Account, pounds
from mmsim.prices import generate_price_path


def demo() -> None:
    n_steps = 12
    half_spread_pence = 100
    prices = generate_price_path(n_steps=n_steps, seed=7)
    customer_rng = random.Random(11)
    account = Account()

    print("One potential customer per step; each quote offers one share.")
    print("Customer limits are printed here, but the quoting rule never sees them.")
    print("P&L is marked AFTER the next price move; inventory and cash include the fill.")
    print(f"{'Step':>4} {'Ref':>8} {'Bid':>8} {'Ask':>8} {'Customer':>8} "
          f"{'Limit':>8} {'Our fill':>9} {'Next ref':>9} {'Inv':>4} {'Cash':>10} {'P&L':>8}")

    for step in range(n_steps):
        reference = prices[step]

        # Quote first, using only the current reference, not the customer or future.
        bid, ask = fixed_quotes(reference, half_spread_pence)
        customer = generate_customer(reference, customer_rng)
        fill = execute_customer(account, customer, bid, ask)

        # The next price becomes available only after the trade decision.
        next_reference = prices[step + 1]
        print(f"{step:>4} {pounds(reference):>8} {pounds(bid):>8} {pounds(ask):>8} "
              f"{customer.side:>8} {pounds(customer.limit_pence):>8} {fill:>9} "
              f"{pounds(next_reference):>9} {account.inventory:>4} "
              f"{pounds(account.cash_pence):>10} {pounds(account.pnl_pence(next_reference)):>8}")


if __name__ == "__main__":
    demo()

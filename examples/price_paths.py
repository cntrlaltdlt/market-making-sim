"""See one price path affect long, flat and short accounts.

The opening trades at the reference price are controlled setup trades, not
simulated customer fills. No further trading happens during this demo.
"""

from mmsim.ledger import Account, pounds
from mmsim.prices import generate_price_path


def demo() -> None:
    prices = generate_price_path(
        start_price_pence=10_000,
        n_steps=20,
        move_pence=10,
        seed=7,
    )

    long_account = Account()
    flat_account = Account()
    short_account = Account()

    # Open equal and opposite positions at £100, with initial P&L of zero.
    long_account.buy(quantity=10, price_pence=prices[0])
    short_account.sell(quantity=10, price_pence=prices[0])

    print("Same price path; no trades after setup. All accounts start at £1,000 equity.")
    print(f"{'Step':>4} {'Reference':>12} {'Long 10 P&L':>14} "
          f"{'Flat P&L':>14} {'Short 10 P&L':>14}")

    # Only the current price is used to value each account.
    for step, reference_price in enumerate(prices):
        print(f"{step:>4} {pounds(reference_price):>12} "
              f"{pounds(long_account.pnl_pence(reference_price)):>14} "
              f"{pounds(flat_account.pnl_pence(reference_price)):>14} "
              f"{pounds(short_account.pnl_pence(reference_price)):>14}")


if __name__ == "__main__":
    demo()

"""Trace cash, inventory, equity and P&L through a few hand-written trades."""
from mmsim.ledger import Account, pounds


def demo() -> None:
    account = Account()
    print(f"{'Event':<23} {'Cash':>12} {'Inventory':>10} {'Reference':>12} {'Equity':>12} {'P&L':>10}")

    def show(event: str, reference: int) -> None:
        print(f"{event:<23} {pounds(account.cash_pence):>12} "
              f"{account.inventory:>10} {pounds(reference):>12} "
              f"{pounds(account.equity_pence(reference)):>12} "
              f"{pounds(account.pnl_pence(reference)):>10}")

    show("Start", 10_000)
    account.sell(quantity=2, price_pence=10_100)
    show("Sell 2 at £101", 10_300)
    account.buy(quantity=1, price_pence=10_200)
    show("Buy 1 at £102", 10_300)


if __name__ == "__main__":
    demo()

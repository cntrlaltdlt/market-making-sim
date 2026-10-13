"""Fees on fills and a costed final exit, using illustrative costs."""

from mmsim.ledger import Account, pounds
from mmsim.experiments import run_experiment, strategy_statistics


def worked_example() -> None:
    account = Account(fee_pence_per_share=10)
    account.buy(quantity=2, price_pence=9_900)
    account.sell(quantity=1, price_pence=10_100)
    reference = 9_800
    print("Worked example: £1,000 start; buy 2 at £99; sell 1 at £101; reference £98")
    print(f"Before closing: cash {pounds(account.cash_pence)}, inventory {account.inventory}, "
          f"marked P&L {pounds(account.pnl_pence(reference))}, fees {pounds(account.total_fees_pence)}")
    settlement = account.close_position(reference, exit_cost_pence_per_share=25)
    print(f"Close {settlement['quantity']} share at {pounds(settlement['execution_price'])}; "
          f"closing fee {pounds(settlement['closing_fee'])}")
    print(f"After closing: cash {pounds(account.cash_pence)}, inventory {account.inventory}, "
          f"final P&L {pounds(settlement['final_pnl'])}\n")


def demo() -> None:
    worked_example()
    # Illustrative assumptions, not fees calibrated to a real exchange.
    fee_pence_per_share = 10
    exit_cost_pence_per_share = 25
    print("500 runs x 200 steps; half-spread £1; adjustment 20p/share; experiment seed 2026")
    print(f"Trading fee {fee_pence_per_share}p/share on each buy/sell, including the exit")
    print(f"Final exit price is {exit_cost_pence_per_share}p/share worse than reference\n")
    gross_results = run_experiment()
    net_results = run_experiment(fee_pence_per_share=fee_pence_per_share,
                                 exit_cost_pence_per_share=exit_cost_pence_per_share)
    for strategy in ("fixed", "adjusted"):
        gross = strategy_statistics(gross_results, strategy)
        net = strategy_statistics(net_results, strategy)
        print(f"{strategy}: mean gross marked P&L {pounds(gross['mean_pnl'])}; "
              f"mean net closed P&L {pounds(net['mean_pnl'])}; "
              f"mean cost {pounds(gross['mean_pnl'] - net['mean_pnl'])}")
    print("The paired scenarios and quoting rules are unchanged; no parameter tuning for costs yet.")


if __name__ == "__main__":
    demo()

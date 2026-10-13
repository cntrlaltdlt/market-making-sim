"""Step through one paired run of fixed and inventory-skewed quotes."""
from mmsim.ledger import pounds
from mmsim.simulation import run_comparison, summarise


def demo() -> None:
    fixed_history, adjusted_history = run_comparison(
        n_steps=40,
        half_spread_pence=100,
        skew_pence_per_share=20,  # Explicit arguments override the function's defaults.
        price_seed=7,
        customer_seed=11,
    )

    print("Separate accounts, identical potential customers and reference prices.")
    print("Quotes use inventory BEFORE the trade; inventory and marked P&L below are AFTER it.")
    print(f"{'Step':>4} {'Strategy':<10} {'Bid':>9} {'Ask':>9} {'Our fill':>10} {'Inv':>5} {'P&L':>10}")
    for step in range(len(fixed_history)):
        for name, history in (("Fixed", fixed_history), ("Adjusted", adjusted_history)):
            row = history[step]
            print(f"{step:>4} {name:<10} {pounds(row['bid']):>9} {pounds(row['ask']):>9} "
                  f"{row['fill']:>10} {row['inventory']:>5} {pounds(row['pnl']):>10}")

    print("\nSingle-run summary (not evidence of general superiority):")
    for name, history in (("Fixed", fixed_history), ("Adjusted", adjusted_history)):
        result = summarise(history)
        print(f"{name}: P&L {pounds(result['final_pnl'])}, trades {result['trades']}, "
              f"mean |inventory| {result['mean_absolute_inventory']:.2f}, "
              f"max |inventory| {result['maximum_absolute_inventory']}")


if __name__ == "__main__":
    demo()

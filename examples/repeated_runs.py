"""500 paired runs with a wide spread and strong skew, printed as a summary."""
from mmsim.experiments import paired_statistics, run_experiment, strategy_statistics
from mmsim.ledger import pounds


def demo() -> None:
    # Change experiment settings HERE. They are passed explicitly below.
    n_runs = 500
    n_steps = 200
    half_spread_pence = 100
    skew_pence_per_share = 20
    experiment_seed = 2026

    results = run_experiment(n_runs, n_steps, half_spread_pence,
                             skew_pence_per_share, experiment_seed)
    print(f"{n_runs} paired runs × {n_steps} steps; experiment seed {experiment_seed}")
    print(f"Half-spread {half_spread_pence}p; adjustment {skew_pence_per_share}p/share")
    print("Reference starts at £100; independent ±10p moves; starting equity £1,000.")
    print("One customer per step; limits within ±150p; no fees or closing costs.\n")

    for strategy in ("fixed", "adjusted"):
        stats = strategy_statistics(results, strategy)
        print(strategy.upper())
        print(f"  Mean final P&L: {pounds(stats['mean_pnl'])}")
        print(f"  P&L standard deviation: {pounds(stats['pnl_standard_deviation'])}")
        print(f"  Losing runs: {stats['loss_fraction']:.1%}")
        print(f"  Worst {stats['worst_tail_count']} runs, mean P&L: {pounds(stats['worst_tail_mean_pnl'])}")
        print(f"  Mean absolute inventory: {stats['mean_absolute_inventory']:.2f} shares")
        print(f"  Mean trades per run: {stats['mean_trades']:.2f}\n")

    paired = paired_statistics(results)
    print("PAIRED COMPARISON (adjusted minus fixed)")
    print(f"  Mean P&L difference: {pounds(paired['mean_pnl_difference'])}")
    print(f"  Adjusted higher-P&L runs: {paired['adjusted_win_fraction']:.1%}")
    print(f"  Tied runs: {paired['tie_fraction']:.1%}")
    interval = paired["approx_95_mean_interval"]
    if interval is not None:
        print(f"  Approximate 95% interval for mean difference: {pounds(interval[0])} to {pounds(interval[1])}")
    print("\nExploratory results for this model. Keep fresh scenarios for final evaluation.")


if __name__ == "__main__":
    demo()

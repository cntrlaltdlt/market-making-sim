"""Exploratory stress scenarios: bigger shocks, drift and one-sided flow."""
from mmsim.experiments import run_experiment, strategy_statistics, paired_statistics
from mmsim.ledger import pounds


def demo():
    settings = dict(n_runs=500, n_steps=200, half_spread_pence=100,
                    skew_pence_per_share=20, experiment_seed=2026,
                    fee_pence_per_share=10, exit_cost_pence_per_share=25,
                    position_limit=3)
    # Change one feature at a time before testing combinations.
    scenarios = [
        ("Baseline", 10, 0, 0.5),
        ("Larger price shocks", 30, 0, 0.5),
        ("Upward tendency", 10, 2, 0.5),
        ("Downward tendency", 10, -2, 0.5),
        ("More customer buyers", 10, 0, 0.8),
        ("More customer sellers", 10, 0, 0.2),
        ("Upward tendency + more buyers", 30, 2, 0.8),
        ("Downward tendency + more sellers", 30, -2, 0.2),
    ]
    print("500 runs × 200 steps per scenario; both strategies limited to ±3 shares")
    print("10p/share fees; 25p/share exit cost; all positions closed")
    for name, move, drift, buy_probability in scenarios:
        results = run_experiment(**settings, move_pence=move,
                                 drift_pence=drift, buy_probability=buy_probability)
        print(f"\n{name}: shock ±{move}p, drift {drift}p, buyer probability {buy_probability}")
        for strategy in ("fixed", "adjusted"):
            stats = strategy_statistics(results, strategy)
            print(f"  {strategy}: mean {pounds(stats['mean_pnl'])}, "
                  f"SD {pounds(stats['pnl_standard_deviation'])}, "
                  f"losing runs {stats['loss_fraction']:.1%}, "
                  f"mean |inventory| {stats['mean_absolute_inventory']:.2f}")
        paired = paired_statistics(results)
        low, high = paired['approx_95_mean_interval']
        print(f"  Adjusted minus fixed: {pounds(paired['mean_pnl_difference'])}; "
              f"approximate 95% mean interval [{pounds(low)}, {pounds(high)}]")
    print("\nExploratory model checks, not evidence of real-world profitability.")
    print("Customers remain uninformed about the next random price shock.")


if __name__ == '__main__':
    demo()

"""Perfectly informed customers as a deliberately strong stress test."""
from mmsim.experiments import run_experiment, strategy_statistics, paired_statistics
from mmsim.ledger import pounds


def demo():
    # ±30p moves stay positive over every possible 200-step path from £100.
    # Narrower quotes let a 30p information advantage cross the spread.
    settings = dict(n_runs=500, n_steps=200, move_pence=30,
                    half_spread_pence=10, skew_pence_per_share=2,
                    position_limit=3, fee_pence_per_share=1,
                    exit_cost_pence_per_share=10, experiment_seed=2026)
    print("500 × 200 steps; ±30p moves; 10p half-spread; 2p/share skew")
    print("Cap ±3; 1p/share fee; 10p/share exit cost; no drift; all positions closed")
    print("Same settings and seeds in every row; only informed fraction changes.")
    for fraction in (0.0, 0.1, 0.25, 0.5):
        results = run_experiment(**settings, informed_fraction=fraction)
        print(f"\nInformed fraction: {fraction:.0%}")
        for strategy in ('fixed', 'adjusted'):
            stats = strategy_statistics(results, strategy)
            print(f"  {strategy}: mean {pounds(stats['mean_pnl'])}, "
                  f"SD {pounds(stats['pnl_standard_deviation'])}, "
                  f"losses {stats['loss_fraction']:.1%}")
        stats = paired_statistics(results)
        low, high = stats['approx_95_mean_interval']
        print(f"  Adjusted minus fixed {pounds(stats['mean_pnl_difference'])}; "
              f"95% mean interval [{pounds(low)}, {pounds(high)}]")
    print("\nPerfect foresight is an artificial stress assumption, not a real-market estimate.")


if __name__ == '__main__':
    demo()

"""Separate the effect of a hard position limit from the effect of inventory skew."""

from mmsim.experiments import run_experiment, strategy_statistics, paired_statistics
from mmsim.ledger import pounds


def demo():
    # All three strategies use these same scenarios and costs.
    settings = {
        "n_runs": 500,
        "n_steps": 200,
        "half_spread_pence": 100,
        "skew_pence_per_share": 20,
        "experiment_seed": 2026,
        "fee_pence_per_share": 10,
        "exit_cost_pence_per_share": 25,
    }
    position_limit = 3
    # **settings passes each dictionary entry as a named function argument.
    unlimited = run_experiment(**settings)
    limited = run_experiment(**settings, position_limit=position_limit)

    print(f"500 matched runs of 200 steps; position limit ±{position_limit} shares")
    print("10p fee per share, 25p exit cost per share; all ending positions closed")
    print("Costs and market settings are illustrative model assumptions.\n")
    for label, results, strategy in (
        ("Fixed, unlimited", unlimited, "fixed"),
        ("Fixed, limited", limited, "fixed"),
        ("Adjusted, limited", limited, "adjusted"),
    ):
        stats = strategy_statistics(results, strategy)
        print(f"{label}: mean P&L {pounds(stats['mean_pnl'])}, "
              f"P&L SD {pounds(stats['pnl_standard_deviation'])}, "
              f"mean |inventory| {stats['mean_absolute_inventory']:.2f}, "
              f"mean trades {stats['mean_trades']:.2f}")

    # Reuse the paired calculation: 'adjusted' is the comparison arm here.
    cap_pairs = []
    for baseline, capped in zip(unlimited, limited):
        assert baseline['price_seed'] == capped['price_seed']
        assert baseline['customer_seed'] == capped['customer_seed']
        cap_pairs.append({"fixed": baseline["fixed"], "adjusted": capped["fixed"]})
    for label, pairs in (("Effect of limit on fixed quotes", cap_pairs),
                         ("Effect of skew with the same limit", limited)):
        stats = paired_statistics(pairs)
        low, high = stats["approx_95_mean_interval"]
        print(f"\n{label}: {pounds(stats['mean_pnl_difference'])}; "
              f"95% interval for mean difference {pounds(low)} to {pounds(high)}")
    print("\nExploratory results for this artificial market; not final evaluation.")


if __name__ == "__main__":
    demo()

"""Repeat paired simulations and measure variation across runs.

All monetary results remain in pence until displayed. These experiments describe
the simulated market, not a real one. Defaults use zero fees and leave ending
positions marked at the reference price; the studies pass explicit costs.
"""

import math
import random
from statistics import mean, stdev

from mmsim.simulation import run_comparison, summarise
from mmsim.ledger import pounds, require_integer


def run_experiment(
    n_runs: int = 500,
    n_steps: int = 200,
    half_spread_pence: int = 100,
    skew_pence_per_share: int = 20,
    experiment_seed: int = 2026,
    fee_pence_per_share: int = 0,
    exit_cost_pence_per_share: int | None = None,
    position_limit: int | None = None,
    move_pence: int = 10,
    drift_pence: int = 0,
    buy_probability: float = 0.5,
    informed_fraction: float = 0.0,
) -> list[dict]:
    """Create fresh accounts and new paired market scenarios on every run.

    The experiment seed controls a generator that supplies price/customer seeds.
    Keep it fixed when changing strategy parameters, so the scenarios stay fixed.
    A model error stops the experiment; failed scenarios are never skipped.
    """
    require_integer(n_runs, "number of runs", minimum=2)
    require_integer(n_steps, "number of steps", minimum=1)
    require_integer(half_spread_pence, "half-spread", minimum=1)
    require_integer(skew_pence_per_share, "inventory adjustment", minimum=0)
    require_integer(experiment_seed, "experiment seed")
    seed_rng = random.Random(experiment_seed)
    results = []

    for run in range(n_runs):
        price_seed = seed_rng.getrandbits(64)
        customer_seed = seed_rng.getrandbits(64)
        fixed_history, adjusted_history = run_comparison(
            n_steps=n_steps,
            half_spread_pence=half_spread_pence,
            skew_pence_per_share=skew_pence_per_share,
            price_seed=price_seed,
            customer_seed=customer_seed,
            fee_pence_per_share=fee_pence_per_share,
            exit_cost_pence_per_share=exit_cost_pence_per_share,
            position_limit=position_limit,
            move_pence=move_pence,
            drift_pence=drift_pence,
            buy_probability=buy_probability,
            informed_fraction=informed_fraction,
        )
        results.append({
            "run": run,
            "price_seed": price_seed,
            "customer_seed": customer_seed,
            "fixed": summarise(fixed_history),
            "adjusted": summarise(adjusted_history),
        })

    return results


def strategy_statistics(results: list[dict], strategy: str) -> dict:
    """Summarise final outcomes across runs, not individual time steps.

    The empirical worst-tail average uses the lowest ceil(5% * n_runs) P&Ls.
    It may be positive; it is not necessarily a loss or a theoretical quantile.
    """
    if len(results) < 2:
        raise ValueError("at least two runs are needed to measure variability")
    if strategy not in ("fixed", "adjusted"):
        raise ValueError("strategy must be 'fixed' or 'adjusted'")
    pnls = []
    inventories = []
    trade_counts = []
    losing_runs = 0

    for result in results:
        summary = result[strategy]
        pnls.append(summary["final_pnl"])
        inventories.append(summary["mean_absolute_inventory"])
        trade_counts.append(summary["trades"])
        if summary["final_pnl"] < 0:
            losing_runs += 1

    worst_count = math.ceil(0.05 * len(pnls))
    worst_pnls = sorted(pnls)[:worst_count]
    return {
        "mean_pnl": mean(pnls),
        "pnl_standard_deviation": stdev(pnls),
        "loss_fraction": losing_runs / len(pnls),
        "worst_tail_mean_pnl": mean(worst_pnls),
        "worst_tail_count": worst_count,
        "mean_absolute_inventory": mean(inventories),
        "mean_trades": mean(trade_counts),
    }


def paired_statistics(results: list[dict]) -> dict:
    """Measure adjusted-minus-fixed P&L for each matching scenario.

    The 95% interval is a large-sample normal approximation for the MEAN
    difference, not a range containing 95% of individual outcomes. It measures
    Monte Carlo sampling uncertainty only, not errors in the market model.
    """
    if len(results) < 2:
        raise ValueError("at least two runs are needed")
    differences = []
    wins = 0
    ties = 0
    for result in results:
        difference = result["adjusted"]["final_pnl"] - result["fixed"]["final_pnl"]
        differences.append(difference)
        if difference > 0:
            wins += 1
        elif difference == 0:
            ties += 1

    average_difference = mean(differences)
    standard_error = stdev(differences) / math.sqrt(len(differences))
    # The normal approximation is unreliable for very small samples.
    interval = None
    if len(differences) >= 30:
        interval = (average_difference - 1.96 * standard_error,
                    average_difference + 1.96 * standard_error)
    return {
        "mean_pnl_difference": average_difference,
        "standard_error": standard_error,
        "approx_95_mean_interval": interval,
        "adjusted_win_fraction": wins / len(differences),
        "tie_fraction": ties / len(differences),
    }

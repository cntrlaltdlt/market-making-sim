"""Choose a skew on development runs, freeze it, then evaluate it on fresh runs.

    python -m studies.selection_study --output results/selection_v1

Run once per output directory. Inspecting evaluation results uses up that
holdout: changing the rule afterwards makes subsequent work exploratory.
"""
import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from statistics import mean, variance

from mmsim.experiments import run_experiment, strategy_statistics, paired_statistics
from mmsim.ledger import pounds

CANDIDATES = (0, 2, 5, 10)
MARKETS = [
    {'name': 'balanced', 'settings': {}},
    {'name': 'informed', 'settings': {'informed_fraction': 0.25}},
    {'name': 'buyers', 'settings': {'buy_probability': 0.8}},
    {'name': 'buyers_and_rising', 'settings': {'buy_probability': 0.8, 'drift_pence': 2}},
]
COMMON = dict(n_steps=200, half_spread_pence=10, move_pence=30,
              fee_pence_per_share=1, exit_cost_pence_per_share=10, position_limit=3)


def choose_skew(scores):
    """Largest development mean wins; exact ties favour the smaller skew."""
    return max(scores, key=lambda skew: (scores[skew], -skew))


def seed_pairs(experiment_seed, n_runs):
    rng = random.Random(experiment_seed)
    return [(rng.getrandbits(64), rng.getrandbits(64)) for _ in range(n_runs)]


def check_seed_split(development_seeds, evaluation_seeds, n_dev, n_eval):
    dev = [pair for seed in development_seeds for pair in seed_pairs(seed, n_dev)]
    test = [pair for seed in evaluation_seeds for pair in seed_pairs(seed, n_eval)]
    # Also reject reuse of either price or customer stream across the split.
    if ({p for p, _ in dev} & {p for p, _ in test}
            or {c for _, c in dev} & {c for _, c in test}):
        raise ValueError('development and evaluation streams overlap')


def aggregate_comparison(groups):
    """Equal-weight mean over fixed regimes; independent runs within each.

    SE uses within-regime variances, respecting the stratified design.
    This interval concerns a frozen strategy, not the selected development score.
    """
    differences = [[r['adjusted']['final_pnl'] - r['fixed']['final_pnl']
                    for r in group] for group in groups]
    average = mean(mean(values) for values in differences)
    se = math.sqrt(sum(variance(values) / len(values) for values in differences)) / len(groups)
    return dict(mean_pnl_difference=average, standard_error=se,
                approx_95_mean_interval=[average-1.96*se, average+1.96*se])


ROOT = Path(__file__).resolve().parents[1]


def source_hashes(relative_paths):
    """SHA-256 of each source file, so saved results can be tied to the exact code."""
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in relative_paths}


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)


def run_study(output):
    # New directories only: never silently overwrite an inspected evaluation.
    output.mkdir(parents=True, exist_ok=False)
    n_dev, n_eval = 300, 500
    dev_seeds = [11001, 11002, 11003, 11004]
    eval_seeds = [91001, 91002, 91003, 91004]
    check_seed_split(dev_seeds, eval_seeds, n_dev, n_eval)
    source_names = ['studies/selection_study.py', 'mmsim/experiments.py', 'mmsim/simulation.py',
                    'mmsim/customers.py', 'mmsim/strategies.py', 'mmsim/prices.py', 'mmsim/ledger.py']
    hashes = source_hashes(source_names)
    protocol = dict(candidates=CANDIDATES, markets=MARKETS, common=COMMON,
                    development_runs_per_market=n_dev, evaluation_runs_per_market=n_eval,
                    development_seeds=dev_seeds, evaluation_seeds=eval_seeds,
                    selection_rule='Highest equal-weight mean net P&L; ties choose smaller skew',
                    comparator='Fixed quotes (zero skew), same spread/costs/cap',
                    source_sha256=hashes)
    save(output/'protocol.json', protocol)  # Before either stage runs.
    scores, development = {}, {}
    for skew in CANDIDATES:
        per_market = []
        for market, seed in zip(MARKETS, dev_seeds):
            runs = run_experiment(**COMMON, **market['settings'], n_runs=n_dev,
                                  experiment_seed=seed, skew_pence_per_share=skew)
            per_market.append(strategy_statistics(runs, 'adjusted')['mean_pnl'])
        scores[skew] = mean(per_market)
        development[skew] = dict(mean_pnl=scores[skew], market_means=per_market)
        print(f'Development: skew {skew}p/share, average net P&L {pounds(scores[skew])}', flush=True)
    chosen = choose_skew(scores)
    # Freeze the decision on disk BEFORE calling the evaluation scenarios.
    save(output/'selection.json', dict(chosen_skew=chosen, development=development))
    print(f'Frozen adjustment: {chosen}p/share', flush=True)
    groups, report = [], {}
    for market, seed in zip(MARKETS, eval_seeds):
        runs = run_experiment(**COMMON, **market['settings'], n_runs=n_eval,
                              experiment_seed=seed, skew_pence_per_share=chosen)
        save(output/f"runs_{market['name']}.json", runs)
        groups.append(runs)
        report[market['name']] = {strategy: strategy_statistics(runs, strategy)
                                  for strategy in ('fixed', 'adjusted')}
        report[market['name']]['paired'] = paired_statistics(runs)
        fixed = report[market['name']]['fixed']['mean_pnl']
        adjusted = report[market['name']]['adjusted']['mean_pnl']
        print(f"Evaluation {market['name']}: fixed {pounds(fixed)}, selected {pounds(adjusted)}", flush=True)
    aggregate = aggregate_comparison(groups)
    save(output/'evaluation.json', dict(markets=report, aggregate_paired=aggregate))
    low, high = aggregate['approx_95_mean_interval']
    print(f"Equal-weight evaluation advantage: {pounds(aggregate['mean_pnl_difference'])}; "
          f"95% mean interval [{pounds(low)}, {pounds(high)}]")
    print('Evaluation is now inspected. Do not tune on these results and call them untouched.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results'/'selection_v1')
    args = parser.parse_args()
    run_study(args.output)

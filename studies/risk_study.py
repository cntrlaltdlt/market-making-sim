"""Profit-risk follow-up to the selection study, on fresh matched paths.

    python -m studies.risk_study --output results/risk_v1

Designed after inspecting the selection study. It selects no new winner: every
skew is reported in every market.
"""
import argparse
from pathlib import Path
from statistics import NormalDist

from studies.selection_study import CANDIDATES, MARKETS, COMMON, ROOT, check_seed_split, save, source_hashes
from mmsim.experiments import run_experiment, strategy_statistics, paired_statistics


def simultaneous_mean_interval(paired, comparisons=12):
    # Bonferroni across 3 nonzero settings × 4 markets; normal approximation.
    z = NormalDist().inv_cdf(1 - 0.05 / (2 * comparisons))
    centre, se = paired['mean_pnl_difference'], paired['standard_error']
    return [centre-z*se, centre+z*se]


def run_study(output):
    output.mkdir(parents=True, exist_ok=False)
    seeds = [121001, 121002, 121003, 121004]
    old_seeds = [2026, 11001,11002,11003,11004,91001,91002,91003,91004]
    check_seed_split(old_seeds, seeds, 500, 500)
    sources = ['studies/risk_study.py', 'studies/selection_study.py', 'mmsim/experiments.py',
               'mmsim/simulation.py', 'mmsim/customers.py', 'mmsim/strategies.py', 'mmsim/prices.py',
               'mmsim/ledger.py']
    save(output/'protocol.json', dict(
        purpose='Descriptive profit-risk follow-up designed after inspecting the selection study (results/selection_v1)',
        candidates=CANDIDATES, markets=MARKETS, common=COMMON, seeds=seeds,
        runs_per_market=500, selection_rule='None: report all candidates and markets',
        metrics=['mean_pnl','pnl_standard_deviation','loss_fraction',
                 'worst_tail_mean_pnl','mean_absolute_inventory','mean_trades'],
        uncertainty='Approximate Bonferroni simultaneous intervals for 12 paired mean differences only; risk estimates descriptive',
        source_sha256=source_hashes(sources)))
    report = {}
    lines = ['# Profit and risk: follow-up study', '',
        'This follow-up was designed after inspecting the selection study. It preserves that result and selects no new winner.',
        'Fresh matched scenarios; 500 runs of 200 steps per market. All values below are sample estimates.',
        'Half-spread 10p; shock ±30p; cap 3 shares; fee 1p/share; closing cost 10p/share.',
        'Risk comparisons are descriptive. Mean-difference intervals below adjust for all 12 nonzero-skew comparisons.', '']
    for market, seed in zip(MARKETS, seeds):
        rows = {}
        baseline = None
        lines.extend([f"## {market['name']}", '',
            '| Skew (p/share) | Mean P&L (£) | P&L SD (£) | Losing runs | Worst 5% mean (£) | Mean absolute inventory |',
            '|---|---|---|---|---|---|'])
        for skew in CANDIDATES:
            runs = run_experiment(**COMMON, **market['settings'], n_runs=500,
                                  experiment_seed=seed, skew_pence_per_share=skew)
            control = [r['fixed'] for r in runs]
            if baseline is None:
                baseline = control
            elif control != baseline:
                raise ValueError('fixed control changed across candidate settings')
            if skew == 0 and any(r['fixed'] != r['adjusted'] for r in runs):
                raise ValueError('zero skew must match fixed quotes')
            if any(r['adjusted']['maximum_absolute_inventory'] > COMMON['position_limit'] for r in runs):
                raise ValueError('position limit exceeded')
            save(output/f"runs_{market['name']}_{skew}.json", runs)
            stats = strategy_statistics(runs,'adjusted')
            paired = paired_statistics(runs)
            rows[skew] = dict(statistics=stats, paired=paired,
                             family_95_mean_interval=simultaneous_mean_interval(paired) if skew else None)
            lines.append(f"| {skew} | {stats['mean_pnl']/100:.2f} | {stats['pnl_standard_deviation']/100:.2f} | "
                         f"{stats['loss_fraction']:.1%} | {stats['worst_tail_mean_pnl']/100:.2f} | {stats['mean_absolute_inventory']:.2f} |")
        lines.append('')
        for skew in CANDIDATES[1:]:
            low, high = rows[skew]['family_95_mean_interval']
            lines.append(f"- {skew}p minus fixed: approximate simultaneous mean interval £{low/100:.2f} to £{high/100:.2f}")
        lines.append('')
        report[market['name']] = rows
        print(market['name'], {skew: {key: round(value, 3) for key,value in row['statistics'].items()}
                               for skew,row in rows.items()}, flush=True)
    save(output/'results.json', report)
    lines += ['## Interpretation limits', '',
        'Zero skew is the fixed strategy. There is no requirement that a nonzero skew wins.',
        'A lower standard deviation alone does not mean better downside protection: inspect loss frequency and worst-tail results too.',
        'Worst 5% means the average final P&L of the 25 lowest-P&L runs in each 500-run sample, not a guaranteed loss limit.',
        'These paths are fresh, but the market model and parameter choices were informed by earlier experiments.',
        'This is simulation evidence conditional on these assumptions, not real-market backtesting.',
        'Reproducing the saved seeds reproduces the same evidence. Any selection based on these results needs a separately designed evaluation.']
    (output/'REPORT.md').write_text('\n'.join(lines)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'results'/'risk_v1')
    run_study(parser.parse_args().output)

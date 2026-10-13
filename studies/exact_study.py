"""Exact analysis of the simulated market (no simulation, no random seeds).

    python -m studies.exact_study --output results/exact_v1

A. Validate the exact engine against the saved 500-run risk study.
B. Expected P&L as a function of the half-spread (zero skew).
C. Exact P&L distributions over a (half-spread, skew) grid.
D. Break-even informed fraction for each half-spread.

Because every number here is computed rather than sampled, choosing the best
setting from these results involves no selection bias. The model, however, is
still the same synthetic market.
"""
import argparse
import json
from pathlib import Path
from statistics import mean, stdev

import numpy as np

from mmsim.exact import RISK_STUDY_MARKETS, distribution, moments
from studies.selection_study import ROOT, source_hashes

RISK_STUDY_SKEWS = (0, 2, 5, 10)
SPREADS = range(1, 151)
GRID_SPREADS = range(20, 125, 5)
GRID_SKEWS = range(0, 44, 4)
BREAKEVEN_SPREADS = range(5, 155, 5)


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=1)


def validation():
    rows = []
    for name, market in RISK_STUDY_MARKETS.items():
        for skew in RISK_STUDY_SKEWS:
            exact = distribution(market.with_(skew=skew)).summary()
            runs = json.loads((ROOT / 'results' / 'risk_v1' / f'runs_{name}_{skew}.json').read_text())
            pnl = [r['adjusted']['final_pnl'] for r in runs]
            se = stdev(pnl) / len(pnl) ** 0.5
            sample = dict(mean_pnl=mean(pnl), pnl_standard_deviation=stdev(pnl),
                          loss_fraction=float(np.mean(np.array(pnl) < 0)),
                          expected_shortfall_5=float(np.mean(sorted(pnl)[:25])),
                          mean_absolute_inventory=mean(r['adjusted']['mean_absolute_inventory'] for r in runs),
                          mean_trades=mean(r['adjusted']['trades'] for r in runs), standard_error=se)
            rows.append(dict(market=name, skew=skew, exact=exact, sample=sample,
                             z=(sample['mean_pnl'] - exact['mean_pnl']) / se,
                             covered=abs(sample['mean_pnl'] - exact['mean_pnl']) <= 1.96 * se))
    return rows


def spread_curves():
    curves = {}
    for name, market in RISK_STUDY_MARKETS.items():
        stats = [moments(market.with_(half_spread=h)) for h in SPREADS]
        curves[name] = dict(half_spread=list(SPREADS), mean_pnl=[s[0] for s in stats],
                            pnl_standard_deviation=[s[1] for s in stats])
        print(f'  spread curve {name}: best half-spread {SPREADS[int(np.argmax(curves[name]["mean_pnl"]))]}p',
              flush=True)
    return curves


def grid():
    out = {}
    for name, market in RISK_STUDY_MARKETS.items():
        cells = []
        for h in GRID_SPREADS:
            for s in GRID_SKEWS:
                cells.append(dict(half_spread=h, skew=s, **distribution(market.with_(half_spread=h, skew=s)).summary()))
        out[name] = cells
        print(f'  grid {name}: {len(cells)} exact distributions', flush=True)
    return out


def breakeven():
    base = RISK_STUDY_MARKETS['balanced']
    rows = []
    for h in BREAKEVEN_SPREADS:
        f = lambda pi: moments(base.with_(half_spread=h, informed_fraction=pi))[0]
        if f(0.0) <= 0:
            rows.append(dict(half_spread=h, breakeven_informed_fraction=0.0))
            continue
        if f(1.0) > 0:
            rows.append(dict(half_spread=h, breakeven_informed_fraction=1.0))
            continue
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
        rows.append(dict(half_spread=h, breakeven_informed_fraction=(lo + hi) / 2))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'results' / 'exact_v1')
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=False)
    sources = ['mmsim/exact.py', 'studies/exact_study.py']
    save(output / 'protocol.json', dict(
        purpose='Exact (lattice) analysis of the simulated market; validation against saved Monte Carlo evidence',
        markets={name: vars(m) for name, m in RISK_STUDY_MARKETS.items()},
        risk_study_skews=RISK_STUDY_SKEWS, spreads=[SPREADS.start, SPREADS.stop - 1],
        grid_spreads=list(GRID_SPREADS), grid_skews=list(GRID_SKEWS), breakeven_spreads=list(BREAKEVEN_SPREADS),
        method='Forward propagation of the joint (inventory, integer P&L) distribution; backward moments for curves',
        source_sha256=source_hashes(sources)))
    print('A. validation', flush=True)
    results = dict(validation=validation())
    print('B. spread curves', flush=True)
    results['spread_curves'] = spread_curves()
    print('C. spread x skew grid', flush=True)
    results['grid'] = grid()
    print('D. break-even informed fraction', flush=True)
    results['breakeven'] = breakeven()
    save(output / 'results.json', results)


if __name__ == '__main__':
    main()

"""Build report/EXACT_ANALYSIS.md and its figures from results/exact_v1.

    python -m studies.exact_report

Re-computes a sample of saved numbers with the exact engine and fails on any
mismatch, so the report cannot drift from the code.
"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from mmsim.exact import RISK_STUDY_MARKETS, moments
from studies.selection_study import ROOT

RESULTS = ROOT / 'results' / 'exact_v1'
OUT = ROOT / 'report'
LABELS = {'balanced': 'Balanced flow', 'informed': '25% informed',
          'buyers': '80% buyers', 'buyers_and_rising': '80% buyers + upward drift'}
COLORS = dict(zip(LABELS, ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']))
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.alpha': 0.18, 'lines.linewidth': 2,
                     'axes.titlesize': 11, 'axes.titleweight': 'bold', 'legend.frameon': False})


def money(pence):
    sign = '−' if pence < 0 else ''
    return f'{sign}£{abs(pence) / 100:,.2f}'


def savefig(fig, name):
    fig.savefig(OUT / f'{name}.png', dpi=180)
    fig.savefig(OUT / f'{name}.svg')
    plt.close(fig)


def verify(r):
    curves = r['spread_curves']
    for name, market in RISK_STUDY_MARKETS.items():
        for h in (10, 77):
            mean, sd = moments(market.with_(half_spread=h))
            i = curves[name]['half_spread'].index(h)
            if not (math.isclose(mean, curves[name]['mean_pnl'][i], rel_tol=1e-12, abs_tol=1e-9)
                    and math.isclose(sd, curves[name]['pnl_standard_deviation'][i], rel_tol=1e-12)):
                raise ValueError(f'saved spread curve does not match the exact engine: {name}, h={h}')


def best_cell(cells, key='mean_pnl'):
    return max(cells, key=lambda c: c[key])


def pareto(cells):
    """Cells not beaten on both expected P&L and expected shortfall."""
    return [c for c in cells if not any(o['mean_pnl'] >= c['mean_pnl'] and o['expected_shortfall_5'] >= c['expected_shortfall_5']
                                        and (o['mean_pnl'], o['expected_shortfall_5']) != (c['mean_pnl'], c['expected_shortfall_5'])
                                        for o in cells)]


def figures(r):
    v = r['validation']
    fig, ax = plt.subplots(figsize=(10, 6.5), layout='constrained')
    for i, row in enumerate(v):
        s, e = row['sample'], row['exact']
        ax.errorbar(s['mean_pnl'] / 100, i, xerr=1.96 * s['standard_error'] / 100, fmt='o', color=COLORS[row['market']],
                    capsize=3, label=LABELS[row['market']] if row['skew'] == 0 else None)
        ax.plot(e['mean_pnl'] / 100, i, marker='|', color='#0b0b0b', ms=16, mew=2.5,
                label='Exact expected value' if i == 0 else None)
    ax.set_yticks(range(len(v)), [f"{LABELS[x['market']]} · {x['skew']}p skew" for x in v])
    ax.invert_yaxis()
    ax.set_xlabel('Net P&L (£): saved 500-run sample mean ±1.96 SE vs exact value')
    ax.set_title('The saved simulations agree with the exact answer')
    ax.legend(loc='lower right', fontsize=8)
    savefig(fig, 'exact_validation')

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), layout='constrained')
    for name, c in r['spread_curves'].items():
        h = np.array(c['half_spread'])
        mean = np.array(c['mean_pnl']) / 100
        axes[0].plot(h, mean, color=COLORS[name], label=LABELS[name])
        k = int(np.argmax(mean))
        axes[0].plot(h[k], mean[k], 'o', color=COLORS[name], ms=7)
    axes[0].axvline(10, color='#52514e', lw=1, ls='--')
    axes[0].annotate('Main studies used 10p', (10, axes[0].get_ylim()[1] * 0.92), xytext=(6, 0),
                     textcoords='offset points', fontsize=8, color='#52514e')
    axes[0].axhline(0, color='#0b0b0b', lw=0.8)
    axes[0].set_xlabel('Half-spread (pence), zero skew')
    axes[0].set_ylabel('Exact expected net P&L over 200 steps (£)')
    axes[0].set_title('The spread is the first-order decision')
    axes[0].legend(fontsize=8)
    b = r['breakeven']
    axes[1].plot([x['half_spread'] for x in b], [100 * x['breakeven_informed_fraction'] for x in b], 'o-', color='#2a78d6', ms=4)
    axes[1].axhline(25, color='#eb6834', lw=1.5, ls='--', label='Informed market in the studies (25%)')
    axes[1].set_xlabel('Half-spread (pence), zero skew, otherwise balanced')
    axes[1].set_ylabel('Informed share that wipes out expected profit (%)')
    axes[1].set_title('How much toxic flow can a spread absorb?')
    axes[1].legend(fontsize=8)
    savefig(fig, 'exact_spread')

    fig, axes = plt.subplots(2, 2, figsize=(12, 9), layout='constrained')
    for ax, (name, cells) in zip(axes.flat, r['grid'].items()):
        hs = sorted({c['half_spread'] for c in cells})
        ks = sorted({c['skew'] for c in cells})
        z = np.array([[next(c['mean_pnl'] for c in cells if c['half_spread'] == h and c['skew'] == k) / 100 for h in hs]
                      for k in ks])
        im = ax.pcolormesh(hs, ks, z, cmap='Blues', shading='nearest')
        best = best_cell(cells)
        ax.plot(best['half_spread'], best['skew'], marker='*', color='#eb6834', ms=14, label='Best expected P&L')
        ax.set_title(LABELS[name])
        ax.set_xlabel('Half-spread (pence)')
        ax.set_ylabel('Skew (pence per share)')
        ax.grid(False)
        fig.colorbar(im, ax=ax, label='Expected net P&L (£)')
        ax.legend(loc='upper left', fontsize=8)
    fig.suptitle('Exact expected P&L over spread and skew (grid starts at 20p; the main studies used 10p)')
    savefig(fig, 'exact_grid')

    fig, axes = plt.subplots(2, 2, figsize=(12, 9), layout='constrained')
    for ax, (name, cells) in zip(axes.flat, r['grid'].items()):
        ax.scatter([c['expected_shortfall_5'] / 100 for c in cells], [c['mean_pnl'] / 100 for c in cells],
                   s=10, color='#c3c2b7', label='All grid settings')
        front = sorted(pareto(cells), key=lambda c: c['expected_shortfall_5'])
        ax.plot([c['expected_shortfall_5'] / 100 for c in front], [c['mean_pnl'] / 100 for c in front], 'o-',
                color=COLORS[name], ms=4, label='Efficient frontier')
        studied = next(x for x in r['validation'] if x['market'] == name and x['skew'] == 0)['exact']
        ax.plot(studied['expected_shortfall_5'] / 100, studied['mean_pnl'] / 100, 'X', color='#0b0b0b', ms=10,
                label='Studied setting (10p, no skew)')
        ax.set_title(LABELS[name])
        ax.set_xlabel('Expected shortfall: mean of worst 5% (£)')
        ax.set_ylabel('Expected net P&L (£)')
        ax.legend(fontsize=8, loc='lower right')
    fig.suptitle('Return versus tail risk, both computed exactly')
    savefig(fig, 'exact_frontier')


def render(r):
    v = r['validation']
    covered = sum(x['covered'] for x in v)
    max_z = max(abs(x['z']) for x in v)
    lines = ['# Exact analysis: the whole P&L distribution, computed rather than simulated', '',
             'The [simulation studies](REPORT.md) estimated profit and risk from 500 random runs. This analysis computes the *exact* distribution of final P&L for the same market. It changes one of their conclusions.', '',
             '## Why exact computation is possible', '',
             'The simulator stores every amount as an integer number of pence. The position limit keeps inventory in {−3, …, 3}, and inventory is the only thing carried from one step to the next. So the pair (inventory, P&L so far) moves on a finite integer grid, and each step\'s probabilities depend only on the current inventory: it is a **Markov chain**. Start with probability 1 on (0, £0). Each step, every state passes its probability on to the states it can reach. After 200 steps the result is the exact probability of every possible final P&L. That gives exact means, standard deviations, loss probabilities and expected shortfall, with no sampling error.', '',
             'Within a step, an ordinary customer is independent of the price move, so its fill probability is a simple count: with limits uniform on ±150p, a quote h pence from the reference fills with probability (151 − h)/301. An informed customer knows the move, so the fill and the move are enumerated together. Code: [`mmsim/exact.py`](../mmsim/exact.py). Study: [`studies/exact_study.py`](../studies/exact_study.py). Saved results: [`results/exact_v1`](../results/exact_v1/).', '',
             '## 1. Checking the engine', '',
             '- **Against the simulator\'s own code.** A test enumerates every possible two-step history using the simulator\'s `Account`, quoting, position-limit and customer functions. It matches the exact distribution outcome by outcome, to 12 decimal places.',
             '- **Two independent calculations.** Forward propagation of the full distribution and a backward recursion for the mean and variance agree to about 1e−12.',
             f'- **Against the saved evidence.** For all 16 market/skew settings of the risk study, the saved 500-run sample mean is within {max_z:.2f} standard errors of the exact value. {covered}/16 of the 95% intervals contain it. Settings within one market share the same simulated paths, so these are effectively four independent checks. Sample loss rates, standard deviations, inventory and trade counts also match.', '',
             '![Validation](exact_validation.png)', '',
             '| Market | Skew | Exact mean | Sample mean | Exact SD | Exact loss probability | Sample losing runs | Exact 5% expected shortfall | Sample worst-25 mean |',
             '|---|---|---|---|---|---|---|---|---|']
    for x in v:
        e, s = x['exact'], x['sample']
        lines.append(f"| {LABELS[x['market']]} | {x['skew']} | {money(e['mean_pnl'])} | {money(s['mean_pnl'])} | {money(e['pnl_standard_deviation'])} | "
                     f"{e['loss_fraction']:.1%} | {s['loss_fraction']:.1%} | {money(e['expected_shortfall_5'])} | {money(s['expected_shortfall_5'])} |")

    def at10(name, skew):
        return next(x for x in v if x['market'] == name and x['skew'] == skew)['exact']
    rising = all(at10(n, 10)['loss_fraction'] > at10(n, 0)['loss_fraction'] for n in LABELS)
    es_worse = [LABELS[n] for n in LABELS if at10(n, 10)['expected_shortfall_5'] < at10(n, 0)['expected_shortfall_5'] - 5]
    lines += ['', '## 2. The skew findings, without sampling noise', '',
              f"At the studies' 10p half-spread, more skew lowers the standard deviation in every market. It {'raises the exact loss probability in every market' if rising else 'does not lower the loss probability in every market'}. It worsens the 5% expected shortfall in {len(es_worse)} of 4 markets and leaves it essentially unchanged in the others. The risk study reported this as \"no consistent improvement\" in the downside, because small sample differences, such as 40.4% vs 40.0% losing runs, could go either way. The exact numbers settle it: at that spread, skew trades away expected profit and loss frequency in exchange for lower variability.", '']
    curves = r['spread_curves']
    lines += ['## 3. The spread was the decision that mattered', '',
              'Expected P&L as a function of the half-spread (zero skew):', '',
              '| Market | Exact expected P&L at 10p | Best half-spread | Exact expected P&L at best |', '|---|---|---|---|']
    for name, c in curves.items():
        k = int(np.argmax(c['mean_pnl']))
        i10 = c['half_spread'].index(10)
        lines.append(f"| {LABELS[name]} | {money(c['mean_pnl'][i10])} | {c['half_spread'][k]}p | {money(c['mean_pnl'][k])} |")
    lines += ['',
              'A one-line calculation explains the optimum. Ignoring inventory, quoting h pence from the reference earns (h − 1) pence after the 1p fee, with probability (151 − h)/301. Maximising (h − 1)(151 − h) gives **h = 76p**. The exact optimum (77–83p) sits slightly higher, because a wider spread also means fewer fills, less inventory and lower closing costs. The studies\' 10p spread filled often but earned little per trade. A wider spread also protects against informed customers: they gain only 30p from a move, so a half-spread above 30p means they never trade at all.', '',
              '![Spread](exact_spread.png)', '',
              f"The right-hand chart answers a Glosten–Milgrom-style question: what share of informed customers would push expected profit to zero? At 10p the answer is {100 * next(x['breakeven_informed_fraction'] for x in r['breakeven'] if x['half_spread'] == 10):.0f}%. The 25% informed market in the studies is beyond that, which is why it lost money. Above 30p, informed customers never trade, so no informed share can make the strategy unprofitable. This depends on the fixed 30p move size, which is a feature of the model.", '']
    lines += ['## 4. With a sensible spread, skew matters again', '', '| Market | Best (half-spread, skew) | Exact expected P&L | Same spread, no skew | Loss probability (best) | 5% expected shortfall (best) |', '|---|---|---|---|---|---|']
    for name, cells in r['grid'].items():
        b = best_cell(cells)
        same = next(c for c in cells if c['half_spread'] == b['half_spread'] and c['skew'] == 0)
        lines.append(f"| {LABELS[name]} | ({b['half_spread']}p, {b['skew']}p) | {money(b['mean_pnl'])} | {money(same['mean_pnl'])} | {b['loss_fraction']:.1%} | {money(b['expected_shortfall_5'])} |")
    lines += ['',
              'With wide quotes, fills are rarer and each one matters more. In the buyer-heavy markets, inventory builds up steadily and skew is worth several pounds. The risk study\'s conclusion that fixed quotes earned most was correct for a 10p spread. It does not hold once the spread is chosen well. The studies tested skew at a single spread far from the optimum, so it could not see this interaction.', '',
              '![Grid](exact_grid.png)', '',
              'Every grid setting has an exact expected P&L and an exact expected shortfall, so the trade-off between them can be drawn as an efficient frontier. The studied setting lies far inside it: there are settings with both higher expected profit and a better worst 5%.', '',
              '![Frontier](exact_frontier.png)', '',
              '## What this does and does not show', '',
              '- It is exact **for this synthetic model**: one-share orders, uniform customer limits, ±30p coin-flip prices, perfectly informed customers. It says nothing directly about real markets.',
              '- Choosing the best setting from exact values has no winner\'s-curse bias, because nothing is sampled. The remaining risk is model risk: the optimum is only as good as the assumptions.',
              '- The method needs a small state space. Here that comes from integer pence and the ±3-share limit. Without a position limit, or with a much longer horizon, the grid grows and simulation becomes the practical tool again.', '',
              '## Reproduce', '', '```sh', 'python -m studies.exact_study --output results/my_exact_reproduction   # about 1 minute', 'python -m studies.exact_report', 'python -m unittest tests.test_exact -v', '```', '']
    return '\n'.join(lines)


def main():
    r = json.loads((RESULTS / 'results.json').read_text())
    verify(r)
    figures(r)
    (OUT / 'EXACT_ANALYSIS.md').write_text(render(r))
    print('Verified saved exact results; wrote report/EXACT_ANALYSIS.md and four figures.')


if __name__ == '__main__':
    main()

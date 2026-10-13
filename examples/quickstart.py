"""The project in one command: simulate, explain, check exactly, then improve.

    python -m examples.quickstart

Uses the 25% informed market from the studies (10p half-spread, ±3 share limit,
1p fee, 10p closing cost, ±30p price moves) and finishes in a few seconds.
"""
import random
import time
from statistics import mean, stdev

from mmsim.attribution import pnl_breakdown
from mmsim.exact import RISK_STUDY_MARKETS, distribution, moments
from mmsim.ledger import pounds
from mmsim.simulation import run_comparison

N_RUNS = 300
SEED = 2026


def simulate(n_runs: int, seed: int) -> list[dict]:
    """Paired runs of fixed quotes in the informed market, with P&L attribution."""
    seed_rng = random.Random(seed)
    breakdowns = []
    for _ in range(n_runs):
        fixed, _ = run_comparison(
            n_steps=200, half_spread_pence=10, skew_pence_per_share=0,
            price_seed=seed_rng.getrandbits(64), customer_seed=seed_rng.getrandbits(64),
            fee_pence_per_share=1, exit_cost_pence_per_share=10, position_limit=3,
            move_pence=30, informed_fraction=0.25)
        breakdowns.append(pnl_breakdown(fixed))
    return breakdowns


def main() -> None:
    start = time.perf_counter()
    market = RISK_STUDY_MARKETS['informed']

    print(f'1. Simulate {N_RUNS} runs of 200 steps: fixed 10p quotes, 25% informed customers')
    runs = simulate(N_RUNS, SEED)
    pnl = [r['final_pnl'] for r in runs]
    se = stdev(pnl) / len(pnl) ** 0.5
    print(f'   mean final P&L {pounds(mean(pnl))} (standard error {pounds(se)}); '
          f'{sum(p < 0 for p in pnl) / len(pnl):.0%} of runs lose money')

    print('\n2. Why: the P&L attribution, averaged over runs')
    print(f'   execution edge  {pounds(mean(r["execution_edge"] for r in runs)):>8}   (earned at the moment of each trade)')
    print(f'   inventory P&L   {pounds(mean(r["inventory_pnl"] for r in runs)):>8}   (prices then move against the position)')
    costs = mean(r['customer_fees'] + r['closing_fees'] + r['closing_execution_cost'] for r in runs)
    print(f'   fees and exit   {pounds(-costs):>8}')

    print('\n3. Check: the exact expected value, computed as a Markov chain (no sampling)')
    exact = distribution(market)
    z = (mean(pnl) - exact.mean) / se
    print(f'   exact mean {pounds(exact.mean)}, exact chance of a loss {exact.loss_probability:.1%}; '
          f'simulated mean is {z:+.1f} standard errors away')

    print('\n4. Improve: exact expected P&L for every half-spread from 1p to 150p')
    curve = [(moments(market.with_(half_spread=h))[0], h) for h in range(1, 151)]
    best_pnl, best_h = max(curve)
    print(f'   best half-spread {best_h}p: expected P&L {pounds(best_pnl)} '
          f'(vs {pounds(exact.mean)} at 10p); above 30p informed customers never trade')

    print(f'\nFinished in {time.perf_counter() - start:.1f} s. Full studies: see README.')


if __name__ == '__main__':
    main()

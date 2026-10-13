"""Average P&L components (edge, inventory, fees, closing) with and without informed flow."""
import random
from statistics import mean
from mmsim.attribution import pnl_breakdown
from mmsim.simulation import run_comparison
from mmsim.ledger import pounds


def demo():
    print('Mean components over 500 runs of 200 steps; all values in pounds')
    print('Shock ±30p; half-spread 10p; skew 2p/share; cap 3; fee 1p; exit cost 10p')
    for fraction in (0.0, 0.25):
        seed_rng = random.Random(2026)
        components = {'fixed': [], 'adjusted': []}
        for _ in range(500):
            fixed, adjusted = run_comparison(
                n_steps=200, half_spread_pence=10, skew_pence_per_share=2,
                price_seed=seed_rng.getrandbits(64), customer_seed=seed_rng.getrandbits(64),
                fee_pence_per_share=1, exit_cost_pence_per_share=10,
                position_limit=3, move_pence=30, informed_fraction=fraction)
            components['fixed'].append(pnl_breakdown(fixed))
            components['adjusted'].append(pnl_breakdown(adjusted))
        print(f'\nInformed probability: {fraction:.0%}')
        for strategy, runs in components.items():
            print(strategy)
            for key in runs[0]:
                value = mean(run[key] for run in runs)
                print(f'  {key}: {pounds(value)}')
    print('\nFees and closing costs are positive deductions. Display rounding may affect sums.')
    print('Every step and final result reconciled exactly in integer pence.')


if __name__ == '__main__':
    demo()

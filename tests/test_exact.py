import copy
import unittest
from collections import defaultdict

import numpy as np

from mmsim.customers import Customer, execute_customer, informed_customer
from mmsim.exact import Distribution, Market, distribution, moments, transitions
from mmsim.ledger import Account
from mmsim.strategies import apply_position_limit, inventory_quotes


def brute_force(m: Market) -> dict[int, float]:
    """Enumerate every history with the simulator's own functions; return the P&L distribution."""
    result = defaultdict(float)
    n = 2 * m.max_offset + 1

    def step(account, reference, steps_left, prob):
        if steps_left == 0:
            if m.exit_cost is not None:
                account.close_position(reference, m.exit_cost)
            result[account.pnl_pence(reference)] += prob
            return
        bid, ask = inventory_quotes(reference, account.inventory, m.half_spread, m.skew)
        bid, ask = apply_position_limit(bid, ask, account.inventory, m.position_limit)
        for direction in (1, -1):
            nxt = reference + m.drift + direction * m.move
            customers = [(informed_customer(reference, nxt), m.informed_fraction)]
            for side, p_side in (('buy', m.buy_probability), ('sell', 1 - m.buy_probability)):
                for offset in range(-m.max_offset, m.max_offset + 1):
                    customers.append((Customer(side, reference + offset), (1 - m.informed_fraction) * p_side / n))
            for customer, p in customers:
                if p == 0:
                    continue
                branch = copy.deepcopy(account)
                if customer is not None:
                    execute_customer(branch, customer, bid, ask)
                step(branch, nxt, steps_left - 1, prob * 0.5 * p)

    step(Account(fee_pence_per_share=m.fee), 10_000, m.n_steps, 1.0)
    return result


class ExactTests(unittest.TestCase):
    def test_matches_brute_force_enumeration_of_simulator_code(self):
        m = Market(n_steps=2, half_spread=3, skew=2, fee=1, exit_cost=4, position_limit=1, move=5,
                   drift=1, buy_probability=0.7, informed_fraction=0.3, max_offset=6)
        expected = brute_force(m)
        d = distribution(m)
        got = dict(zip(d.pnl.tolist(), d.prob.tolist()))
        self.assertEqual(set(got), {k for k, v in expected.items() if v > 0})
        for pnl, p in expected.items():
            self.assertAlmostEqual(got[pnl], p, places=12)

    def test_one_step_closed_form(self):
        # Flat start, no informed flow or drift: each side fills with probability
        # (M + 1 - h) / (2M + 1) and earns h - fee.
        for h in (1, 10, 75, 150):
            m = Market(n_steps=1, half_spread=h, exit_cost=None)
            self.assertAlmostEqual(moments(m)[0], (h - 1) * (151 - h) / 301, places=10)

    def test_forward_and_backward_agree(self):
        for m in (Market(n_steps=40), Market(n_steps=40, informed_fraction=0.25, skew=5),
                  Market(n_steps=40, buy_probability=0.8, drift=2, half_spread=60, skew=12)):
            d = distribution(m)
            self.assertAlmostEqual(d.prob.sum(), 1.0, places=12)
            mean, sd = moments(m)
            self.assertAlmostEqual(d.mean, mean, places=8)
            self.assertAlmostEqual(d.sd, sd, places=8)

    def test_transition_probabilities_sum_to_one(self):
        m = Market(informed_fraction=0.4, buy_probability=0.8, drift=2, skew=7)
        for q in range(-3, 4):
            self.assertAlmostEqual(sum(p for p, *_ in transitions(m, q)), 1.0, places=12)
            self.assertTrue(all(abs(q2) <= 3 for _, q2, _, _ in transitions(m, q)))

    def test_expected_shortfall_and_quantile(self):
        d = Distribution(np.array([-100, 0, 50]), np.array([0.02, 0.48, 0.5]), 0, 0)
        self.assertAlmostEqual(d.expected_shortfall(0.05), (-100 * 0.02 + 0 * 0.03) / 0.05)
        self.assertEqual(d.quantile(0.4), 0)
        self.assertAlmostEqual(d.loss_probability, 0.02)


if __name__ == '__main__':
    unittest.main()

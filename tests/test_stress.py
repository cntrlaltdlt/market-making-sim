import random
import unittest
from mmsim.prices import generate_price_path
from mmsim.customers import generate_customer
from mmsim.experiments import run_experiment


class StressTests(unittest.TestCase):
    def test_drift_adds_exactly_per_step_with_same_shocks(self):
        baseline = generate_price_path(n_steps=100, seed=42)
        drifted = generate_price_path(n_steps=100, seed=42, drift_pence=2)
        self.assertEqual(drifted, [price + 2 * step for step, price in enumerate(baseline)])

    def test_shock_size_and_deterministic_drift(self):
        prices = generate_price_path(n_steps=100, move_pence=30, drift_pence=-2)
        self.assertTrue(all(b-a in (-32, 28) for a, b in zip(prices, prices[1:])))
        self.assertEqual(generate_price_path(n_steps=2, move_pence=0, drift_pence=2), [10000,10002,10004])

    def test_side_probability_endpoints(self):
        for probability, side in ((0, 'sell'), (1, 'buy')):
            rng = random.Random(7)
            for _ in range(100):
                customer = generate_customer(10000, rng, buy_probability=probability)
                self.assertEqual(customer.side, side)
                self.assertTrue(9850 <= customer.limit_pence <= 10150)

    def test_invalid_probability_and_drift(self):
        for value in (-0.1, 1.1, float('nan'), True, '0.5'):
            with self.assertRaises(ValueError):
                generate_customer(10000, random.Random(7), buy_probability=value)
        with self.assertRaises(TypeError):
            generate_price_path(drift_pence=0.5)

    def test_stressed_zero_skew_matches_and_seeds_replay(self):
        settings = dict(n_runs=10, n_steps=200, move_pence=30, drift_pence=2,
                        buy_probability=0.8, position_limit=3, skew_pence_per_share=0,
                        fee_pence_per_share=10, exit_cost_pence_per_share=25)
        results = run_experiment(**settings)
        self.assertEqual(results, run_experiment(**settings))
        for row in results:
            self.assertEqual(row['fixed'], row['adjusted'])
            self.assertLessEqual(row['fixed']['maximum_absolute_inventory'], 3)


if __name__ == '__main__':
    unittest.main()

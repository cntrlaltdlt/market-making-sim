"""Check path mechanics, reproducibility and the link to inventory risk."""

import random
import unittest
from unittest.mock import patch

from mmsim.ledger import Account
from mmsim.prices import generate_price_path


class PriceTests(unittest.TestCase):
    def test_path_includes_start_and_exactly_requested_moves(self):
        prices = generate_price_path(n_steps=50, move_pence=10)
        self.assertEqual(len(prices), 51)
        self.assertEqual(prices[0], 10_000)
        self.assertTrue(all(abs(b - a) == 10 for a, b in zip(prices, prices[1:])))

    def test_seed_replays_the_same_scenario_without_touching_global_rng(self):
        state = random.getstate()
        first = generate_price_path(seed=42)
        second = generate_price_path(seed=42)
        self.assertEqual(first, second)
        self.assertEqual(state, random.getstate())

    def test_no_steps_or_no_movement(self):
        self.assertEqual(generate_price_path(n_steps=0), [10_000])
        self.assertEqual(generate_price_path(n_steps=3, move_pence=0), [10_000] * 4)

    def test_nonpositive_price_fails_instead_of_silently_biasing_the_path(self):
        with patch("mmsim.prices.random.Random") as factory:
            factory.return_value.choice.return_value = -1
            with self.assertRaisesRegex(ValueError, "zero or below"):
                generate_price_path(start_price_pence=10, n_steps=1, move_pence=10)

    def test_invalid_inputs(self):
        for kwargs in [dict(start_price_pence=0), dict(n_steps=-1),
                       dict(move_pence=-1), dict(n_steps=1.5), dict(seed="7")]:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises((ValueError, TypeError)):
                    generate_price_path(**kwargs)

    def test_fixed_inventory_exposure_on_every_step(self):
        prices = generate_price_path()
        long_account, flat_account, short_account = Account(), Account(), Account()
        long_account.buy(5, prices[0])
        short_account.sell(5, prices[0])
        for price in prices:
            self.assertEqual(long_account.pnl_pence(price), 5 * (price - prices[0]))
            self.assertEqual(short_account.pnl_pence(price), -5 * (price - prices[0]))
            self.assertEqual(flat_account.pnl_pence(price), 0)
        self.assertEqual(long_account.cash_pence, 50_000)
        self.assertEqual(long_account.inventory, 5)
        self.assertEqual(short_account.cash_pence, 150_000)
        self.assertEqual(short_account.inventory, -5)


if __name__ == "__main__":
    unittest.main()

import unittest

from mmsim.simulation import run_comparison
from mmsim.customers import Customer, execute_customer
from mmsim.ledger import Account
from mmsim.strategies import apply_position_limit


class PositionLimitTests(unittest.TestCase):
    def test_correct_side_withdrawn(self):
        self.assertEqual(apply_position_limit(9900, 10100, 3, 3), (None, 10100))
        self.assertEqual(apply_position_limit(9900, 10100, -3, 3), (9900, None))
        self.assertEqual(apply_position_limit(9900, 10100, 2, 3), (9900, 10100))
        self.assertEqual(apply_position_limit(9900, 10100, 0, 0), (None, None))

    def test_withdrawn_quote_has_no_fill_or_fee_but_can_reduce_inventory(self):
        for inventory, blocked_side, permitted_side in ((3, 'sell', 'buy'), (-3, 'buy', 'sell')):
            account = Account(fee_pence_per_share=10)
            account.inventory = inventory
            bid, ask = apply_position_limit(9900, 10100, inventory, 3)
            cash = account.cash_pence
            limit = 9800 if blocked_side == 'sell' else 10200
            self.assertEqual(execute_customer(account, Customer(blocked_side, limit), bid, ask), 'NO TRADE')
            self.assertEqual((account.cash_pence, account.inventory, account.total_fees_pence), (cash, inventory, 0))
            limit = 9800 if permitted_side == 'sell' else 10200
            execute_customer(account, Customer(permitted_side, limit), bid, ask)
            self.assertEqual(abs(account.inventory), 2)
            self.assertEqual(account.total_fees_pence, 10)

    def test_limits_hold_and_zero_skew_matches(self):
        for seed in range(20):
            for cap in (0, 1, 3):
                fixed, adjusted = run_comparison(n_steps=200, price_seed=seed, customer_seed=seed+100,
                    skew_pence_per_share=0, position_limit=cap, fee_pence_per_share=10,
                    exit_cost_pence_per_share=25)
                self.assertEqual(fixed, adjusted)
                self.assertTrue(all(abs(row['inventory']) <= cap for row in fixed))
                if cap == 0:
                    self.assertTrue(all(row['fill'] == 'NO TRADE' for row in fixed))
                    self.assertEqual(fixed[-1]['settlement']['final_pnl'], 0)
                _, skewed = run_comparison(n_steps=200, price_seed=seed, customer_seed=seed+100,
                    skew_pence_per_share=20, position_limit=cap)
                self.assertTrue(all(abs(row['inventory']) <= cap for row in skewed))

    def test_unreachable_limit_preserves_history(self):
        self.assertEqual(run_comparison(n_steps=100), run_comparison(n_steps=100, position_limit=101))

    def test_invalid_limits(self):
        for cap in (-1, 1.5, True):
            with self.assertRaises((ValueError, TypeError)):
                run_comparison(position_limit=cap)
        with self.assertRaises(ValueError):
            apply_position_limit(9900, 10100, 4, 3)


if __name__ == '__main__':
    unittest.main()

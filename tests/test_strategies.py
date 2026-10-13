import unittest

from mmsim.simulation import run_comparison, summarise
from mmsim.customers import Customer, execute_customer
from mmsim.ledger import Account
from mmsim.strategies import inventory_quotes


class StrategyTests(unittest.TestCase):
    def test_long_short_and_flat_quotes_preserve_spread(self):
        for position, expected in [(5, (9_850, 10_050)), (0, (9_900, 10_100)),
                                   (-5, (9_950, 10_150))]:
            with self.subTest(position=position):
                bid, ask = inventory_quotes(10_000, position, 100, 10)
                self.assertEqual((bid, ask), expected)
                self.assertEqual(ask - bid, 200)

    def test_zero_adjustment_matches_every_fixed_quote_fill_and_balance(self):
        for price_seed, customer_seed in [(7, 11), (2, 19), (42, 3)]:
            fixed, adjusted = run_comparison(skew_pence_per_share=0,
                                             price_seed=price_seed, customer_seed=customer_seed)
            self.assertEqual(fixed, adjusted)

    def test_adjustment_can_enable_inventory_reducing_trade(self):
        account = Account()
        account.buy(5, 10_000)
        customer = Customer("buy", 10_075)
        self.assertEqual(execute_customer(account, customer, 9_900, 10_100), "NO TRADE")
        bid, ask = inventory_quotes(10_000, account.inventory)
        self.assertEqual(execute_customer(account, customer, bid, ask), "WE SELL")
        self.assertEqual(account.inventory, 4)
        self.assertEqual(account.cash_pence, 60_050)

    def test_changing_adjustment_cannot_change_fixed_control_scenario(self):
        fixed_a, _ = run_comparison(skew_pence_per_share=0)
        fixed_b, _ = run_comparison(skew_pence_per_share=20)
        self.assertEqual(fixed_a, fixed_b)

    def test_risk_summary_uses_absolute_inventory(self):
        history = [{"inventory": 2, "fill": "WE BUY", "pnl": 50},
                   {"inventory": -2, "fill": "NO TRADE", "pnl": -30}]
        self.assertEqual(summarise(history), {"final_pnl": -30, "trades": 1,
                                             "mean_absolute_inventory": 2,
                                             "maximum_absolute_inventory": 2})

    def test_empty_run_has_zero_summary(self):
        fixed, adjusted = run_comparison(n_steps=0)
        self.assertEqual(fixed, [])
        self.assertEqual(adjusted, [])
        self.assertEqual(summarise(fixed)["final_pnl"], 0)

    def test_invalid_adjustment_or_nonpositive_quotes_fail(self):
        with self.assertRaises(ValueError):
            inventory_quotes(10_000, 1, skew_pence_per_share=-1)
        with self.assertRaises(TypeError):
            inventory_quotes(10_000, 1.5)
        with self.assertRaises(ValueError):
            inventory_quotes(100, 20)


if __name__ == "__main__":
    unittest.main()

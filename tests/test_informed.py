import unittest
from mmsim.customers import informed_customer, execute_customer
from mmsim.ledger import Account
from mmsim.simulation import run_comparison


class InformedTests(unittest.TestCase):
    def test_up_move_selects_buy_and_costs_market_maker(self):
        customer = informed_customer(10000, 10030)
        self.assertEqual((customer.side, customer.limit_pence), ('buy', 10030))
        account = Account(fee_pence_per_share=1)
        self.assertEqual(execute_customer(account, customer, 9990, 10010), 'WE SELL')
        self.assertEqual(account.pnl_pence(10030), -21)

    def test_down_move_selects_sell_and_costs_market_maker(self):
        customer = informed_customer(10000, 9970)
        account = Account(fee_pence_per_share=1)
        self.assertEqual(execute_customer(account, customer, 9990, 10010), 'WE BUY')
        self.assertEqual(account.pnl_pence(9970), -21)

    def test_no_movement_and_unattractive_quote(self):
        self.assertIsNone(informed_customer(10000, 10000))
        account = Account()
        self.assertEqual(execute_customer(account, informed_customer(10000,10030), 9900,10100), 'NO TRADE')
        self.assertEqual(execute_customer(account, informed_customer(10000,10030), 9990,None), 'NO TRADE')

    def test_zero_fraction_preserves_results(self):
        self.assertEqual(run_comparison(), run_comparison(informed_fraction=0))

    def test_zero_skew_matches_limits_hold_and_pretrade_quotes_ignore_future(self):
        for seed in range(10):
            settings = dict(n_steps=200, price_seed=seed, half_spread_pence=10,
                            move_pence=30, position_limit=3)
            fixed, adjusted = run_comparison(**settings, informed_fraction=0.5)
            self.assertEqual(fixed, adjusted)
            self.assertTrue(all(abs(row['inventory']) <= 3 for row in fixed))
            baseline, _ = run_comparison(**settings, informed_fraction=0)
            self.assertEqual((fixed[0]['bid'], fixed[0]['ask']),
                             (baseline[0]['bid'], baseline[0]['ask']))

    def test_invalid_fraction(self):
        for value in (-1, 1.1, True, float('nan')):
            with self.assertRaises(ValueError):
                run_comparison(informed_fraction=value)


if __name__ == '__main__':
    unittest.main()

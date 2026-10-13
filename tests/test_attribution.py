import unittest
from copy import deepcopy
from mmsim.attribution import pnl_breakdown
from mmsim.simulation import run_comparison, snapshot, summarise
from mmsim.ledger import Account


class AttributionTests(unittest.TestCase):
    def row(self, account, fill, before, after, bid=9990, ask=10010):
        row = snapshot(account, bid, ask, fill, after)
        row.update(reference_before=before, reference_after=after)
        return row

    def test_informed_sell_example_and_closing(self):
        account = Account(fee_pence_per_share=1)
        account.buy(1, 9990)
        history = [self.row(account, 'WE BUY', 10000, 9970)]
        history[-1]['settlement'] = account.close_position(9970, 10)
        self.assertEqual(pnl_breakdown(history), dict(execution_edge=10, inventory_pnl=-30,
            customer_fees=1, closing_fees=1, closing_execution_cost=10, final_pnl=-32))

    def test_short_position_and_no_trade_price_change(self):
        account = Account(fee_pence_per_share=1)
        account.sell(1, 10010)
        history = [self.row(account, 'WE SELL', 10000, 10030)]
        history.append(self.row(account, 'NO TRADE', 10030, 10000))
        self.assertEqual(pnl_breakdown(history)['final_pnl'], 9)
        self.assertEqual(pnl_breakdown(history)['inventory_pnl'], 0)
        self.assertEqual(pnl_breakdown(history)['customer_fees'], 1)

    def test_negative_execution_edge_allowed(self):
        account = Account()
        account.buy(1, 10005)
        result = pnl_breakdown([self.row(account, 'WE BUY', 10000, 10000, bid=10005)])
        self.assertEqual(result['execution_edge'], -5)

    def test_reconcile_across_markets_and_settlement_modes(self):
        for seed in range(10):
            for fraction in (0, 0.25, 1):
                for closing in (None, 0, 10):
                    histories = run_comparison(n_steps=200, price_seed=seed, customer_seed=seed+20,
                        half_spread_pence=10, skew_pence_per_share=2, move_pence=30,
                        drift_pence=2, buy_probability=0.8, informed_fraction=fraction,
                        position_limit=3, fee_pence_per_share=1, exit_cost_pence_per_share=closing)
                    for history in histories:
                        self.assertEqual(pnl_breakdown(history)['final_pnl'], summarise(history)['final_pnl'])

    def test_empty_and_corrupted_records(self):
        self.assertEqual(pnl_breakdown([])['final_pnl'], 0)
        history, _ = run_comparison(exit_cost_pence_per_share=10)
        bad = deepcopy(history)
        bad[0]['pnl'] += 1
        with self.assertRaises(ValueError):
            pnl_breakdown(bad)
        history[-1]['settlement']['final_pnl'] += 1
        with self.assertRaises(ValueError):
            pnl_breakdown(history)


if __name__ == '__main__':
    unittest.main()

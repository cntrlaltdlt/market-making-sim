import unittest
from mmsim.ledger import Account
from mmsim.customers import Customer, execute_customer
from mmsim.simulation import run_comparison, summarise


class CostTests(unittest.TestCase):
    def test_long_worked_example(self):
        a = Account(fee_pence_per_share=10)
        a.buy(2, 9_900)
        a.sell(1, 10_100)
        self.assertEqual((a.cash_pence, a.inventory, a.total_fees_pence), (90_270, 1, 30))
        self.assertEqual(a.pnl_pence(9_800), 70)
        result = a.close_position(9_800, 25)
        self.assertEqual(result['execution_price'], 9_775)
        self.assertEqual(result['final_pnl'], 35)
        self.assertEqual((a.inventory, a.total_fees_pence), (0, 40))

    def test_short_exit_buys_above_reference(self):
        a = Account(fee_pence_per_share=10)
        a.sell(2, 10_100)
        result = a.close_position(10_300, 25)
        self.assertEqual(result['execution_price'], 10_325)
        self.assertEqual(result['final_pnl'], -490)
        self.assertEqual(a.inventory, 0)

    def test_flat_exit_is_free_and_repeat_exit_is_noop(self):
        a = Account(fee_pence_per_share=10)
        self.assertEqual(a.close_position(10_000, 25)['quantity'], 0)
        self.assertEqual(a.cash_pence, 100_000)
        a.buy(1, 9_900)
        a.close_position(10_000, 25)
        cash, fees = a.cash_pence, a.total_fees_pence
        a.close_position(10_000, 25)
        self.assertEqual((a.cash_pence, a.total_fees_pence), (cash, fees))

    def test_rejection_has_no_fee(self):
        a = Account(fee_pence_per_share=10)
        execute_customer(a, Customer('buy', 9_900), 9_950, 10_050)
        self.assertEqual(a.total_fees_pence, 0)

    def test_zero_cost_closing_preserves_pnl_and_risk_metrics(self):
        gross = run_comparison()
        closed = run_comparison(exit_cost_pence_per_share=0)
        for first, second in zip(gross, closed):
            self.assertEqual(summarise(first), summarise(second))

    def test_costs_reconcile_without_changing_fills_or_risk(self):
        gross_pair = run_comparison(n_steps=200, skew_pence_per_share=20)
        net_pair = run_comparison(n_steps=200, skew_pence_per_share=20,
                                  fee_pence_per_share=10, exit_cost_pence_per_share=25)
        for gross, net in zip(gross_pair, net_pair):
            for a,b in zip(gross,net):
                self.assertEqual((a['bid'],a['ask'],a['fill'],a['inventory']),
                                 (b['bid'],b['ask'],b['fill'],b['inventory']))
            g,n=summarise(gross),summarise(net)
            closing_quantity=abs(net[-1]['inventory'])
            self.assertEqual(g['final_pnl']-n['final_pnl'],g['trades']*10+closing_quantity*35)
            self.assertEqual(g['mean_absolute_inventory'],n['mean_absolute_inventory'])
            self.assertEqual(g['trades'],n['trades'])

    def test_zero_skew_matches_with_costs(self):
        a,b=run_comparison(skew_pence_per_share=0,fee_pence_per_share=10,exit_cost_pence_per_share=25)
        self.assertEqual(a,b)

    def test_invalid_costs_and_exit_price_do_not_change_account(self):
        with self.assertRaises(ValueError): Account(fee_pence_per_share=-1)
        a=Account(fee_pence_per_share=10)
        a.buy(1,100)
        before=(a.cash_pence,a.inventory,a.total_fees_pence)
        with self.assertRaises(ValueError): a.close_position(10,20)
        self.assertEqual(before,(a.cash_pence,a.inventory,a.total_fees_pence))


if __name__ == '__main__':
    unittest.main()

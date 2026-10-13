import io
import unittest
from contextlib import redirect_stdout

from examples import quickstart


class QuickstartTests(unittest.TestCase):
    def test_attribution_adds_up_on_every_run(self):
        for run in quickstart.simulate(n_runs=5, seed=1):
            self.assertEqual(run['final_pnl'], run['execution_edge'] + run['inventory_pnl']
                             - run['customer_fees'] - run['closing_fees'] - run['closing_execution_cost'])

    def test_runs_end_to_end(self):
        output = io.StringIO()
        with redirect_stdout(output):
            quickstart.main()
        text = output.getvalue()
        self.assertIn('best half-spread 77p', text)
        self.assertIn('exact mean £-3.79', text)


if __name__ == '__main__':
    unittest.main()

"""Check economic examples, including short positions and invalid fills."""

import unittest

from mmsim.ledger import Account


class LedgerTests(unittest.TestCase):
    def test_worked_example(self):
        account = Account()
        account.buy(2, 9_900)
        account.sell(1, 10_100)
        self.assertEqual(account.cash_pence, 90_300)
        self.assertEqual(account.inventory, 1)
        self.assertEqual(account.equity_pence(9_800), 100_100)
        self.assertEqual(account.pnl_pence(9_800), 100)

    def test_completed_round_trip_no_longer_depends_on_price(self):
        account = Account()
        account.buy(3, 9_900)
        account.sell(3, 10_100)
        self.assertEqual(account.inventory, 0)
        self.assertEqual(account.pnl_pence(9_000), 600)
        self.assertEqual(account.pnl_pence(11_000), 600)

    def test_short_position_loses_when_price_rises(self):
        account = Account()
        account.sell(2, 10_100)
        self.assertEqual(account.inventory, -2)
        self.assertEqual(account.pnl_pence(10_300), -400)
        account.buy(2, 10_300)
        self.assertEqual(account.inventory, 0)
        self.assertEqual(account.pnl_pence(10_000), -400)

    def test_marking_changes_pnl_without_changing_cash_or_inventory(self):
        account = Account()
        account.buy(2, 9_900)
        self.assertEqual(account.pnl_pence(10_100) - account.pnl_pence(10_000), 200)
        self.assertEqual(account.cash_pence, 80_200)
        self.assertEqual(account.inventory, 2)

    def test_invalid_fills_do_not_change_the_account(self):
        account = Account()
        for method in (account.buy, account.sell):
            for quantity, price in [(0, 100), (-1, 100), (1, 0), (1, -100), (1.5, 100), (1, 99.5)]:
                with self.subTest(method=method.__name__, quantity=quantity, price=price):
                    with self.assertRaises((ValueError, TypeError)):
                        method(quantity, price)
                    self.assertEqual(account.cash_pence, 100_000)
                    self.assertEqual(account.inventory, 0)


if __name__ == "__main__":
    unittest.main()

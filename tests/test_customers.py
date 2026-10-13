import random
import unittest

from mmsim.customers import Customer, execute_customer, fixed_quotes, generate_customer
from mmsim.ledger import Account


class CustomerTests(unittest.TestCase):
    def test_buyer_accepts_at_or_above_ask_and_pays_our_quote(self):
        for limit in (10_050, 10_100):
            account = Account()
            self.assertEqual(execute_customer(account, Customer("buy", limit), 9_950, 10_050), "WE SELL")
            self.assertEqual(account.cash_pence, 110_050)
            self.assertEqual(account.inventory, -1)

    def test_seller_accepts_at_or_below_bid_and_receives_our_quote(self):
        for limit in (9_950, 9_900):
            account = Account()
            self.assertEqual(execute_customer(account, Customer("sell", limit), 9_950, 10_050), "WE BUY")
            self.assertEqual(account.cash_pence, 90_050)
            self.assertEqual(account.inventory, 1)

    def test_rejection_one_penny_past_limit_does_not_change_account(self):
        for customer in (Customer("buy", 10_049), Customer("sell", 9_951)):
            account = Account()
            self.assertEqual(execute_customer(account, customer, 9_950, 10_050), "NO TRADE")
            self.assertEqual(account.cash_pence, 100_000)
            self.assertEqual(account.inventory, 0)

    def test_round_trip_captures_spread_and_price_move_exposes_inventory(self):
        account = Account()
        execute_customer(account, Customer("sell", 9_900), 9_950, 10_050)
        self.assertEqual(account.pnl_pence(9_800), -150)
        execute_customer(account, Customer("buy", 10_100), 9_950, 10_050)
        self.assertEqual(account.inventory, 0)
        self.assertEqual(account.pnl_pence(9_800), 100)

    def test_seed_replays_customer_stream_and_limits_stay_in_range(self):
        def stream():
            rng = random.Random(11)
            return [generate_customer(10_000, rng) for _ in range(50)]
        first, second = stream(), stream()
        self.assertEqual([(c.side, c.limit_pence) for c in first], [(c.side, c.limit_pence) for c in second])
        self.assertTrue(all(9_850 <= c.limit_pence <= 10_150 for c in first))

    def test_wider_quotes_cannot_add_fills_for_same_customer(self):
        narrow, wide = fixed_quotes(10_000, 25), fixed_quotes(10_000, 100)
        narrow_count = wide_count = 0
        for side in ("buy", "sell"):
            for limit in range(9_850, 10_151):
                customer = Customer(side, limit)
                narrow_fill = execute_customer(Account(), customer, *narrow) != "NO TRADE"
                wide_fill = execute_customer(Account(), customer, *wide) != "NO TRADE"
                self.assertFalse(wide_fill and not narrow_fill)
                narrow_count += narrow_fill
                wide_count += wide_fill
        self.assertLess(wide_count, narrow_count)

    def test_invalid_customer_and_quotes_are_rejected(self):
        with self.assertRaises(ValueError):
            Customer("hold", 10_000)
        with self.assertRaises(ValueError):
            Customer("buy", 0)
        with self.assertRaises(ValueError):
            fixed_quotes(50, 50)
        account = Account()
        with self.assertRaises(ValueError):
            execute_customer(account, Customer("buy", 10_000), 10_100, 10_000)
        self.assertEqual(account.cash_pence, 100_000)
        self.assertEqual(account.inventory, 0)


if __name__ == "__main__":
    unittest.main()

"""Customers who accept or reject our posted quotes.

Each customer wants one share. 'buy' and 'sell' describe the CUSTOMER's side.
Their limit is private to the environment; our quoting rule must not see it.
"""

import random

from mmsim.ledger import Account, require_integer


class Customer:
    def __init__(self, side: str, limit_pence: int):
        if side not in ("buy", "sell"):
            raise ValueError("customer side must be 'buy' or 'sell'")
        require_integer(limit_pence, "customer limit", minimum=1)
        self.side = side
        self.limit_pence = limit_pence


def generate_customer(
    reference_price_pence: int,
    rng: random.Random,
    max_offset_pence: int = 150,
    buy_probability: float = 0.5,
) -> Customer:
    """Choose a side and a limit within ±max_offset of the current reference.

    Integer offsets are uniformly distributed, including both endpoints.
    Customers do not know the next price change. They may reject our quotes.
    """
    require_integer(reference_price_pence, "reference price", minimum=1)
    require_integer(max_offset_pence, "maximum offset", minimum=0)
    if type(buy_probability) not in (int, float) or not 0 <= buy_probability <= 1:
        raise ValueError("buy probability must be a number between 0 and 1")
    # rng.choice at 0.5 keeps balanced-flow seeds compatible with saved results.
    if buy_probability == 0.5:
        side = rng.choice(["buy", "sell"])
    else:
        side = "buy" if rng.random() < buy_probability else "sell"
    offset = rng.randint(-max_offset_pence, max_offset_pence)
    return Customer(side, reference_price_pence + offset)


def fixed_quotes(reference_price_pence: int, half_spread_pence: int = 100) -> tuple[int, int]:
    """Return our bid and ask, each for one share, around the current reference."""
    require_integer(reference_price_pence, "reference price", minimum=1)
    require_integer(half_spread_pence, "half-spread", minimum=1)
    bid = reference_price_pence - half_spread_pence
    ask = reference_price_pence + half_spread_pence
    if bid <= 0:
        raise ValueError("the bid must remain positive")
    return bid, ask


def execute_customer(account: Account, customer: Customer, bid: int | None, ask: int | None) -> str:
    """Execute at OUR quote, not the customer's limit. Return OUR fill side.

    Every fill is exactly one share, and equality with the limit is accepted.
    'NO TRADE' leaves the account unchanged.
    """
    # None means we are not offering to trade on that side.
    if bid is not None:
        require_integer(bid, "bid", minimum=1)
    if ask is not None:
        require_integer(ask, "ask", minimum=1)
    if bid is not None and ask is not None and bid >= ask:
        raise ValueError("bid must be below ask")

    if customer.side == "buy" and ask is not None and ask <= customer.limit_pence:
        account.sell(quantity=1, price_pence=ask)
        return "WE SELL"

    if customer.side == "sell" and bid is not None and bid >= customer.limit_pence:
        account.buy(quantity=1, price_pence=bid)
        return "WE BUY"

    return "NO TRADE"


def informed_customer(reference_price_pence: int, next_price_pence: int) -> Customer | None:
    """An idealised customer knows the next reference price exactly.

    Their limit is that future value. They still need an executable quote.
    No price change means no informed order. Only the environment calls this;
    quoting strategies must never receive the next price or customer type.
    """
    require_integer(reference_price_pence, "reference price", minimum=1)
    require_integer(next_price_pence, "next price", minimum=1)
    if next_price_pence > reference_price_pence:
        return Customer("buy", next_price_pence)
    if next_price_pence < reference_price_pence:
        return Customer("sell", next_price_pence)
    return None

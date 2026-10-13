"""Quoting rules: inventory skew and position limits."""

from mmsim.customers import fixed_quotes
from mmsim.ledger import require_integer


def inventory_quotes(
    reference_price_pence: int,
    inventory: int,
    half_spread_pence: int = 100,
    skew_pence_per_share: int = 10,
) -> tuple[int, int]:
    """Long inventory lowers both quotes; short inventory raises both.

    The spread stays constant. A zero skew reproduces the fixed strategy.
    This is a quoting preference, not a hard position limit. Strong adjustments
    can quote across the reference price, sacrificing margin to reduce exposure.
    """
    require_integer(reference_price_pence, "reference price", minimum=1)
    require_integer(inventory, "inventory")
    require_integer(skew_pence_per_share, "inventory adjustment", minimum=0)

    shift = inventory * skew_pence_per_share
    quote_centre = reference_price_pence - shift
    return fixed_quotes(quote_centre, half_spread_pence)


def apply_position_limit(
    bid: int,
    ask: int,
    inventory: int,
    position_limit: int | None,
) -> tuple[int | None, int | None]:
    """Withdraw risk-increasing quotes at the limit, for one-share fills.

    None as the limit means unlimited. None as a quote means no offer.
    Apply BEFORE revealing the customer. This limits shares, not losses.
    """
    require_integer(inventory, "inventory")
    if position_limit is None:
        return bid, ask
    require_integer(position_limit, "position limit", minimum=0)
    if abs(inventory) > position_limit:
        raise ValueError("starting inventory is already outside the limit")

    if inventory >= position_limit:
        bid = None  # We cannot buy another share.
    if inventory <= -position_limit:
        ask = None  # We cannot sell another share.
    return bid, ask

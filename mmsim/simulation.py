"""Run fixed and inventory-skewed quotes side by side in the same simulated market.

These accounts are alternative experiments, not competitors sharing an exchange.
Each sees the same customer each step, but can receive a different fill.
"""

import random

from mmsim.customers import execute_customer, fixed_quotes, generate_customer, informed_customer
from mmsim.ledger import Account, require_integer
from mmsim.prices import generate_price_path
from mmsim.strategies import apply_position_limit, inventory_quotes


def snapshot(account: Account, bid: int | None, ask: int | None, fill: str, reference: int) -> dict:
    """Save numbers at this moment, not a reference to the changing account."""
    return {
        "bid": bid,
        "ask": ask,
        "fill": fill,
        "inventory": account.inventory,
        "pnl": account.pnl_pence(reference),
        "fees": account.total_fees_pence,
    }


def run_comparison(
    n_steps: int = 40,
    half_spread_pence: int = 100,
    skew_pence_per_share: int = 0,
    price_seed: int = 7,
    customer_seed: int = 11,
    fee_pence_per_share: int = 0,
    exit_cost_pence_per_share: int | None = None,
    position_limit: int | None = None,
    move_pence: int = 10,
    drift_pence: int = 0,
    buy_probability: float = 0.5,
    informed_fraction: float = 0.0,
) -> tuple[list[dict], list[dict]]:
    if type(informed_fraction) not in (int, float) or not 0 <= informed_fraction <= 1:
        raise ValueError("informed fraction must be between 0 and 1")
    # None retains marked ending inventory; 0 closes exactly at reference.
    if exit_cost_pence_per_share is not None:
        require_integer(exit_cost_pence_per_share, "exit cost", minimum=0)
    if position_limit is not None:
        require_integer(position_limit, "position limit", minimum=0)
    prices = generate_price_path(n_steps=n_steps, seed=price_seed,
                                 move_pence=move_pence, drift_pence=drift_pence)
    customer_rng = random.Random(customer_seed)
    # Independent type draws preserve the original uninformed customer stream.
    type_rng = random.Random(f"informed:{customer_seed}")
    fixed_account = Account(fee_pence_per_share=fee_pence_per_share)
    adjusted_account = Account(fee_pence_per_share=fee_pence_per_share)
    fixed_history = []
    adjusted_history = []

    for step in range(n_steps):
        reference = prices[step]

        # Both quotes are decided before this step's customer is revealed.
        fixed_bid, fixed_ask = fixed_quotes(reference, half_spread_pence)
        adjusted_bid, adjusted_ask = inventory_quotes(
            reference,
            adjusted_account.inventory,
            half_spread_pence,
            skew_pence_per_share,
        )

        fixed_bid, fixed_ask = apply_position_limit(
            fixed_bid, fixed_ask, fixed_account.inventory, position_limit
        )
        adjusted_bid, adjusted_ask = apply_position_limit(
            adjusted_bid, adjusted_ask, adjusted_account.inventory, position_limit
        )

        # Generate ONCE and reuse: no strategy gets a different potential customer.
        customer = generate_customer(reference, customer_rng, buy_probability=buy_probability)
        # Draw the baseline customer every step, even when replacing it.
        # Perfect future information is given ONLY to the environment's customer.
        is_informed = type_rng.random() < informed_fraction
        if is_informed:
            customer = informed_customer(reference, prices[step + 1])
        fixed_fill = "NO TRADE"
        adjusted_fill = "NO TRADE"
        if customer is not None:
            fixed_fill = execute_customer(fixed_account, customer, fixed_bid, fixed_ask)
            adjusted_fill = execute_customer(adjusted_account, customer, adjusted_bid, adjusted_ask)

        next_reference = prices[step + 1]
        fixed_history.append(snapshot(fixed_account, fixed_bid, fixed_ask, fixed_fill, next_reference))
        adjusted_history.append(snapshot(adjusted_account, adjusted_bid, adjusted_ask, adjusted_fill, next_reference))
        # Diagnostic data is recorded after execution, never passed to quotes.
        for history in (fixed_history, adjusted_history):
            history[-1]["reference_before"] = reference
            history[-1]["reference_after"] = next_reference

    if exit_cost_pence_per_share is not None and n_steps > 0:
        # Attach the closing result separately; do not overwrite risk snapshots
        # or count the forced exit as another customer opportunity.
        fixed_history[-1]["settlement"] = fixed_account.close_position(prices[-1], exit_cost_pence_per_share)
        adjusted_history[-1]["settlement"] = adjusted_account.close_position(prices[-1], exit_cost_pence_per_share)
    return fixed_history, adjusted_history


def summarise(history: list[dict]) -> dict:
    """Inventory metrics use all post-trade snapshots; P&L is in pence."""
    trade_count = 0
    total_absolute_inventory = 0
    maximum_absolute_inventory = 0

    for row in history:
        if row["fill"] != "NO TRADE":
            trade_count += 1
        position_size = abs(row["inventory"])
        total_absolute_inventory += position_size
        maximum_absolute_inventory = max(maximum_absolute_inventory, position_size)

    final_pnl = history[-1]["pnl"] if history else 0
    if history and "settlement" in history[-1]:
        final_pnl = history[-1]["settlement"]["final_pnl"]
    return {
        "final_pnl": final_pnl,
        "trades": trade_count,
        "mean_absolute_inventory": total_absolute_inventory / len(history) if history else 0,
        "maximum_absolute_inventory": maximum_absolute_inventory,
    }

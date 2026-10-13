"""Decompose P&L and reconcile every penny to the account ledger.

For a one-share fill: execution edge + post-trade inventory * price change
- customer fee = change in marked P&L. Closing costs are deducted separately.
This is an accounting identity, not a causal estimate of adverse selection.
"""


def pnl_breakdown(history: list[dict]) -> dict:
    totals = dict(execution_edge=0, inventory_pnl=0, customer_fees=0,
                  closing_fees=0, closing_execution_cost=0)
    previous_pnl = 0
    previous_fees = 0
    for row in history:
        reference = row['reference_before']
        edge = 0
        if row['fill'] == 'WE BUY':
            edge = reference - row['bid']
        elif row['fill'] == 'WE SELL':
            edge = row['ask'] - reference
        elif row['fill'] != 'NO TRADE':
            raise ValueError('unknown fill label')

        price_change = row['reference_after'] - reference
        inventory_pnl = row['inventory'] * price_change
        fee = row['fees'] - previous_fees
        change = edge + inventory_pnl - fee
        if change != row['pnl'] - previous_pnl:
            raise ValueError('step P&L does not reconcile with the ledger')
        totals['execution_edge'] += edge
        totals['inventory_pnl'] += inventory_pnl
        totals['customer_fees'] += fee
        previous_pnl = row['pnl']
        previous_fees = row['fees']

    expected_final = previous_pnl
    if history and 'settlement' in history[-1]:
        settlement = history[-1]['settlement']
        totals['closing_fees'] = settlement['closing_fee']
        totals['closing_execution_cost'] = settlement['execution_cost']
        expected_final = settlement['final_pnl']

    totals['final_pnl'] = (totals['execution_edge'] + totals['inventory_pnl']
                           - totals['customer_fees'] - totals['closing_fees']
                           - totals['closing_execution_cost'])
    if totals['final_pnl'] != expected_final:
        raise ValueError('final P&L does not reconcile with the ledger')
    return totals

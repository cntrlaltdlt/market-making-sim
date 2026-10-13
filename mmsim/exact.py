"""Exact P&L distributions for the simulated market, without simulation.

Every amount in this model is an integer number of pence, and the only state
that carries over between steps is inventory, which the position limit keeps
in {-L, ..., L}. So the market maker's (inventory, P&L) pair is a Markov chain
on a finite integer lattice, and its exact distribution after 200 steps can be
computed by pushing probability forward one step at a time.

One step from inventory q (matching comparison_demo.run_comparison exactly):
  quotes   ask = ref + a, bid = ref - b with a = h - q*skew, b = h + q*skew;
           a side is withdrawn when it would breach the position limit
  customer ordinary with probability 1 - pi: buys with probability p_buy, and
           its limit offset U is uniform on {-M, ..., M}; it trades with us
           if our price is at least as good as its limit
           informed with probability pi: knows the next move D and trades
           only if D > 0 (buys) or D < 0 (sells), with limit ref + D
  price    D = drift + move or drift - move, each with probability 1/2
  P&L      edge (a or b) - fee + q_after * D   (the attribution identity)
At the end, any inventory is closed at a cost of (exit cost + fee) per share.

Ordinary customers are independent of the price move. Informed customers are
not, so for them the fill decision and D are enumerated together.
Probabilities are floating point; everything else is exact.
"""
from dataclasses import dataclass, replace


import numpy as np


@dataclass(frozen=True)
class Market:
    n_steps: int = 200
    half_spread: int = 10
    skew: int = 0
    fee: int = 1
    exit_cost: int | None = 10
    position_limit: int = 3
    move: int = 30
    drift: int = 0
    buy_probability: float = 0.5
    informed_fraction: float = 0.0
    max_offset: int = 150

    def with_(self, **changes) -> 'Market':
        return replace(self, **changes)


# The four markets of the risk study, with its common settings.
RISK_STUDY_MARKETS = {
    'balanced': Market(),
    'informed': Market(informed_fraction=0.25),
    'buyers': Market(buy_probability=0.8),
    'buyers_and_rising': Market(buy_probability=0.8, drift=2),
}


def _count_at_least(threshold: int, M: int) -> int:
    """Number of integers U in [-M, M] with U >= threshold."""
    return max(0, min(2 * M + 1, M - max(threshold, -M) + 1))


def transitions(m: Market, q: int) -> list[tuple[float, int, int, int]]:
    """All one-step outcomes from inventory q: (probability, next q, P&L change, fills)."""
    L = m.position_limit
    if abs(q) > L:
        raise ValueError('inventory outside the position limit')
    a = m.half_spread - q * m.skew          # ask minus reference
    b = m.half_spread + q * m.skew          # reference minus bid
    can_sell = q > -L                        # ask quoted
    can_buy = q < L                          # bid quoted
    n = 2 * m.max_offset + 1
    # Ordinary buyer trades if ask <= limit, i.e. U >= a; seller if bid >= limit, i.e. U <= -b.
    p_buyer_fills = _count_at_least(a, m.max_offset) / n if can_sell else 0.0
    p_seller_fills = _count_at_least(b, m.max_offset) / n if can_buy else 0.0   # symmetric U
    pi, pb = m.informed_fraction, m.buy_probability
    out: dict[tuple[int, int, int], float] = {}

    def add(p, q_next, change, fills):
        if p > 0:
            key = (q_next, change, fills)
            out[key] = out.get(key, 0.0) + p

    for D in (m.drift + m.move, m.drift - m.move):
        half = 0.5
        # Ordinary customer (independent of D).
        ordinary = (1 - pi) * half
        add(ordinary * pb * p_buyer_fills, q - 1, a - m.fee + (q - 1) * D, 1)
        add(ordinary * (1 - pb) * p_seller_fills, q + 1, b - m.fee + (q + 1) * D, 1)
        add(ordinary * (pb * (1 - p_buyer_fills) + (1 - pb) * (1 - p_seller_fills)), q, q * D, 0)
        # Informed customer knows D.
        informed = pi * half
        if D > 0 and can_sell and a <= D:
            add(informed, q - 1, a - m.fee + (q - 1) * D, 1)
        elif D < 0 and can_buy and b <= -D:
            add(informed, q + 1, b - m.fee + (q + 1) * D, 1)
        else:
            add(informed, q, q * D, 0)
    return [(p, q_next, change, fills) for (q_next, change, fills), p in out.items()]


def _terminal_cost(m: Market, q: int) -> int:
    return 0 if m.exit_cost is None else abs(q) * (m.exit_cost + m.fee)


@dataclass
class Distribution:
    pnl: np.ndarray          # support, integer pence
    prob: np.ndarray
    mean_abs_inventory: float
    mean_trades: float

    @property
    def mean(self):
        return float(self.prob @ self.pnl)

    @property
    def sd(self):
        return float(np.sqrt(self.prob @ (self.pnl - self.mean) ** 2))

    @property
    def loss_probability(self):
        return float(self.prob[self.pnl < 0].sum())

    def expected_shortfall(self, level=0.05):
        """Mean P&L over the worst `level` of probability mass (fractional at the edge)."""
        cumulative = np.cumsum(self.prob)
        take = np.minimum(self.prob, np.maximum(level - (cumulative - self.prob), 0))
        return float(take @ self.pnl / level)

    def quantile(self, level):
        return int(self.pnl[np.searchsorted(np.cumsum(self.prob), level)])

    def summary(self):
        return dict(mean_pnl=self.mean, pnl_standard_deviation=self.sd, loss_fraction=self.loss_probability,
                    expected_shortfall_5=self.expected_shortfall(0.05), median=self.quantile(0.5),
                    mean_absolute_inventory=self.mean_abs_inventory, mean_trades=self.mean_trades)


def distribution(m: Market) -> Distribution:
    """Exact distribution of final P&L, by forward propagation on the lattice."""
    L = m.position_limit
    qs = range(-L, L + 1)
    table = {q: transitions(m, q) for q in qs}
    lo_step = min(c for t in table.values() for _, _, c, _ in t)
    hi_step = max(c for t in table.values() for _, _, c, _ in t)
    lo = 0                                       # P&L value of column 0
    dist = np.zeros((2 * L + 1, 1))
    dist[L, 0] = 1.0                             # start flat with zero P&L
    abs_inventory = trades = 0.0
    for _ in range(m.n_steps):
        width = dist.shape[1]
        new = np.zeros((2 * L + 1, width + hi_step - lo_step))
        for q in qs:
            row = dist[q + L]
            mass = row.sum()
            if mass == 0:
                continue
            for p, q_next, change, fills in table[q]:
                start = change - lo_step
                new[q_next + L, start:start + width] += p * row
                trades += p * fills * mass
        dist, lo = new, lo + lo_step
        abs_inventory += float(np.abs(np.arange(-L, L + 1)) @ dist.sum(axis=1))
    # Close the remaining inventory, then collapse over inventory.
    width = dist.shape[1]
    max_cost = _terminal_cost(m, L)
    final = np.zeros(width + max_cost)
    for q in qs:
        cost = _terminal_cost(m, q)
        final[max_cost - cost:max_cost - cost + width] += dist[q + L]
    pnl = np.arange(width + max_cost) + lo - max_cost
    keep = final > 0
    return Distribution(pnl[keep], final[keep], abs_inventory / m.n_steps, trades)


def moments(m: Market) -> tuple[float, float]:
    """Exact mean and standard deviation by backward recursion (fast; no lattice)."""
    L = m.position_limit
    qs = np.arange(-L, L + 1)
    table = [transitions(m, int(q)) for q in qs]
    m1 = np.array([-_terminal_cost(m, int(q)) for q in qs], dtype=float)
    m2 = m1 ** 2
    for _ in range(m.n_steps):
        n1, n2 = np.zeros_like(m1), np.zeros_like(m2)
        for i, outcomes in enumerate(table):
            for p, q_next, c, _ in outcomes:
                j = q_next + L
                n1[i] += p * (c + m1[j])
                n2[i] += p * (c * c + 2 * c * m1[j] + m2[j])
        m1, m2 = n1, n2
    mean = m1[L]
    return float(mean), float(np.sqrt(max(m2[L] - mean ** 2, 0.0)))



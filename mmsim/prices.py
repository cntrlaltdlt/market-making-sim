"""Reference price path driven by independent coin flips."""

import random

from mmsim.ledger import require_integer


def generate_price_path(
    start_price_pence: int = 10_000,
    n_steps: int = 20,
    move_pence: int = 10,
    seed: int | None = 7,
    drift_pence: int = 0,
) -> list[int]:
    """Return the starting price followed by n_steps random price updates.

    Each move is drift_pence plus an equally likely ±move_pence shock.
    Drift is the expected change per step, not a guaranteed direction.
    A local random generator makes a seeded run repeatable without changing
    other code's random state. Seed=None requests an unseeded run.

    This additive model can reach non-positive prices. If that happens,
    stop with an error; do not silently clamp prices or discard failed runs.
    """
    require_integer(start_price_pence, "starting price", minimum=1)
    require_integer(n_steps, "number of steps", minimum=0)
    require_integer(move_pence, "move size", minimum=0)
    require_integer(drift_pence, "drift")
    if seed is not None:
        require_integer(seed, "seed")

    rng = random.Random(seed)
    prices = [start_price_pence]

    for _ in range(n_steps):
        direction = rng.choice([-1, 1])
        next_price = prices[-1] + drift_pence + direction * move_pence
        if next_price <= 0:
            raise ValueError(
                "The reference price reached zero or below. "
                "This additive price model is unsuitable for this run; "
                "review the model before continuing the experiment."
            )
        prices.append(next_price)

    return prices

# Profit and risk: follow-up study

This follow-up was designed after inspecting the selection study. It preserves that result and selects no new winner.
Fresh matched scenarios; 500 runs of 200 steps per market. All values below are sample estimates.
Half-spread 10p; shock ±30p; cap 3 shares; fee 1p/share; closing cost 10p/share.
Risk comparisons are descriptive. Mean-difference intervals below adjust for all 12 nonzero-skew comparisons.

## balanced

| Skew (p/share) | Mean P&L (£) | P&L SD (£) | Losing runs | Worst 5% mean (£) | Mean absolute inventory |
|---|---|---|---|---|---|
| 0 | 6.60 | 8.82 | 24.0% | -10.65 | 1.68 |
| 2 | 6.06 | 8.56 | 24.2% | -10.69 | 1.63 |
| 5 | 5.10 | 8.25 | 26.6% | -11.02 | 1.57 |
| 10 | 3.11 | 7.82 | 36.2% | -12.14 | 1.47 |

- 2p minus fixed: approximate simultaneous mean interval £-0.77 to £-0.32
- 5p minus fixed: approximate simultaneous mean interval £-1.82 to £-1.17
- 10p minus fixed: approximate simultaneous mean interval £-3.92 to £-3.06

## informed

| Skew (p/share) | Mean P&L (£) | P&L SD (£) | Losing runs | Worst 5% mean (£) | Mean absolute inventory |
|---|---|---|---|---|---|
| 0 | -4.57 | 8.24 | 70.0% | -21.82 | 1.70 |
| 2 | -5.66 | 8.15 | 75.4% | -22.39 | 1.67 |
| 5 | -7.18 | 7.97 | 83.2% | -23.50 | 1.63 |
| 10 | -9.97 | 7.64 | 91.0% | -25.60 | 1.56 |

- 2p minus fixed: approximate simultaneous mean interval £-1.25 to £-0.94
- 5p minus fixed: approximate simultaneous mean interval £-2.84 to £-2.38
- 10p minus fixed: approximate simultaneous mean interval £-5.75 to £-5.06

## buyers

| Skew (p/share) | Mean P&L (£) | P&L SD (£) | Losing runs | Worst 5% mean (£) | Mean absolute inventory |
|---|---|---|---|---|---|
| 0 | 2.73 | 11.54 | 40.4% | -21.33 | 2.61 |
| 2 | 2.51 | 11.44 | 40.0% | -21.59 | 2.59 |
| 5 | 2.11 | 11.38 | 42.0% | -21.72 | 2.56 |
| 10 | 1.39 | 11.09 | 44.8% | -21.71 | 2.49 |

- 2p minus fixed: approximate simultaneous mean interval £-0.31 to £-0.13
- 5p minus fixed: approximate simultaneous mean interval £-0.77 to £-0.48
- 10p minus fixed: approximate simultaneous mean interval £-1.55 to £-1.14

## buyers_and_rising

| Skew (p/share) | Mean P&L (£) | P&L SD (£) | Losing runs | Worst 5% mean (£) | Mean absolute inventory |
|---|---|---|---|---|---|
| 0 | -6.80 | 11.25 | 73.2% | -29.79 | 2.61 |
| 2 | -6.93 | 11.19 | 73.6% | -29.67 | 2.58 |
| 5 | -7.13 | 11.01 | 74.0% | -29.56 | 2.55 |
| 10 | -7.62 | 10.79 | 76.0% | -29.68 | 2.49 |

- 2p minus fixed: approximate simultaneous mean interval £-0.22 to £-0.03
- 5p minus fixed: approximate simultaneous mean interval £-0.48 to £-0.18
- 10p minus fixed: approximate simultaneous mean interval £-1.03 to £-0.61

## Interpretation limits

Zero skew is the fixed strategy. There is no requirement that a nonzero skew wins.
A lower standard deviation alone does not mean better downside protection: inspect loss frequency and worst-tail results too.
Worst 5% means the average final P&L of the 25 lowest-P&L runs in each 500-run sample, not a guaranteed loss limit.
These paths are fresh, but the market model and parameter choices were informed by earlier experiments.
This is simulation evidence conditional on these assumptions, not real-market backtesting.
Reproducing the saved seeds reproduces the same evidence. Any selection based on these results needs a separately designed evaluation.

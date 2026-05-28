# block3_summary — metric definitions

## Authoritative metric: scheduler-native

The canonical Block 3 allocation-disagreement result uses the
**scheduler-native** definition: each scheduler (GoodSpeed, SSD-aware) produces
its own native allocation, and we compare the relative order `order(k1,k2)`.
At capacity `C=12` on the Alpaca-calibrated grid (5184 cases):

| metric | rate |
|---|---|
| order mismatch (incl. ties) | 51.6% |
| GoodSpeed blindness (GS tie -> SSD non-tie) | 22.8% |
| GoodSpeed overcommit (GS non-tie -> SSD tie) | 18.0% |
| strict reversal (opposite strict orders) | 10.8% |

Strict reversal grows with capacity (C=8: 6.8% -> C=20: 15.7%) and with the
drafter-cost ratio. Strict-reversal cases carry large utility gaps
(avg. 37.4%, max 48.5%).

These numbers are computed by `sim/experiments/block3_make_native_order_figures.py`
from `block3_reversal_alpaca_calibrated/summary.csv`.

## SUPERSEDED: `gate3_summary.csv`

`gate3_summary.csv` reports reversal under the **old comparable-only
definition**, which filters to GoodSpeed allocations that are also executable
under the SSD timing model (`valid` column) and reports the `reversal` column
over that filtered subset. For Alpaca-calibrated this yields a misleadingly low
"2.0% reversal" because the integer-`k` setting funnels most genuine
disagreements into tie/non-tie transitions that the strict-reversal filter
discards.

**Do not quote `gate3_summary.csv` reversal rates or `valid_rate` as results.**
The file is retained only because the legacy `block3_make_slide_figures.py`
still reads it. Use the scheduler-native numbers above for the thesis.

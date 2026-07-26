# NovaSteel scoring worker

This package computes advisory-only lining RUL and quality-risk/what-if results.
It records model-version, uncertainty, and ranked drivers; it never changes a
recipe, setpoint, or OT system.

## Lining RUL model

`physics_features.py` extracts thermal features and fits an ordinary
least-squares wear trend over refractory thickness; `rul_model.py` projects the
fitted slope to the minimum safe lining thickness to obtain P50. The P10/P90
band is derived from the fit residuals and the reported confidence is derived
from r², so a noisier or shorter observation window widens the band and lowers
confidence instead of returning a fixed answer. Changing the thermal input
moves the forecast — there is no hard-coded demo verdict anywhere in the path.

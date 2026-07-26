"""NovaSteel synthetic captor/sensor simulator package.

Deterministic, fully synthetic generator for furnace, rolling, energy,
quality, maintenance, and operator-knowledge data as specified in
``docs/data/synthetic-data-and-simulators.md``.

Every record produced by this package carries
``data_classification: SYNTHETIC`` and ``privacy_label: DEMO-NONPERSONAL``.
This package only depends on the Python standard library.
"""

__version__ = "1.0.0"
GENERATOR_VERSION = f"novasteel-sim/{__version__}"

# NovaSteel optimizer worker

The worker provides a deterministic, constraint-aware energy-dispatch proposal.
It validates hard production constraints, keeps planned tonnage unchanged, and
returns a proposal only. It has no operational schedule-write capability.

It deliberately uses only the Python standard library. When installing any
future dependency, use only `https://packagefeedproxy.microsoft.io/pypi/simple`.

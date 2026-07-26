"""Enable ``python -m simulator`` as an alias for the CLI."""
from simulator.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

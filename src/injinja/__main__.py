# pragma: no cover
"""
USAGE:
python3 -m injinja --help
OR
uv run -m injinja --help
"""

# Standard Library
import sys

from .injinja import main

if __name__ == "__main__":
    main(sys.argv[1:])

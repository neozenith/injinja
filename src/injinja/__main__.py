# pragma: no cover
"""
USAGE:
python3 -m injinja --help
OR
uv run -m injinja --help
"""

# Standard Library
import logging
import sys

from .injinja import log_date_format, log_format, log_level, main

if __name__ == "__main__":
    logging.basicConfig(level=log_level, format=log_format, datefmt=log_date_format)
    main(sys.argv[1:])

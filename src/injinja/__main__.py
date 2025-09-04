# pragma: no cover
"""
USAGE:
python3 -m injinja --help
OR
uv run -m injinja --help
"""

# Standard Library
import sys
import logging
from .injinja import main, log_format, log_date_format, log_level

if __name__ == "__main__":
    logging.basicConfig(level=log_level, format=log_format, datefmt=log_date_format)
    main(sys.argv[1:])

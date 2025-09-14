#!/usr/bin/env python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "toml",
# ]
# ///

"""Update Python version specifications in pyproject.toml to support multiple versions.

This script updates the project metadata to indicate support for Python 3.12 and 3.13.
"""

import argparse
import sys
from pathlib import Path
from textwrap import dedent

SCRIPT = Path(__file__)
SCRIPT_NAME = SCRIPT.stem
SCRIPT_DIR = SCRIPT.parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent

PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"

# Target Python versions to support
PYTHON_VERSIONS = ["3.12", "3.13"]


def update_pyproject_toml(dry_run: bool = False) -> bool:
    """Update pyproject.toml to include support for multiple Python versions."""
    if not PYPROJECT_PATH.exists():
        print(f"Error: {PYPROJECT_PATH} not found")
        return False
    
    content = PYPROJECT_PATH.read_text()
    
    # Update classifiers to include Python 3.13
    if '"Programming Language :: Python :: 3.13"' not in content:
        # Find the line with Python 3.12 classifier and add 3.13 after it
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '"Programming Language :: Python :: 3.12"' in line:
                # Insert Python 3.13 after 3.12
                lines.insert(i + 1, '  "Programming Language :: Python :: 3.13",')
                break
        
        updated_content = '\n'.join(lines)
        
        if dry_run:
            print("DRY RUN: Would update pyproject.toml with:")
            print("+ Added Python 3.13 classifier")
            return True
        else:
            PYPROJECT_PATH.write_text(updated_content)
            print("✅ Updated pyproject.toml to include Python 3.13 support")
            return True
    else:
        print("✅ pyproject.toml already includes Python 3.13 support")
        return True


def main(dry_run: bool = False):
    """Update Python version support in the project."""
    print(f"Updating Python version support for: {', '.join(PYTHON_VERSIONS)}")
    
    success = update_pyproject_toml(dry_run)
    
    if success and not dry_run:
        print("\n📝 Next steps:")
        print("1. Run 'make test-matrix' to test all Python/Jinja2 combinations locally")
        print("2. The GitHub Actions workflow will automatically test the matrix on push/PR")
        print("3. Consider running 'uv sync' to ensure lock file is updated")
    
    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(f"""\
        {SCRIPT_NAME} - Update Python version support in pyproject.toml.
        
        This script adds Python 3.13 to the supported versions in pyproject.toml
        classifiers, enabling testing against multiple Python versions.
        
        Target Python versions: {', '.join(PYTHON_VERSIONS)}
        """)
    )
    parser.add_argument("-n", "--dry-run", action="store_true", 
                       help="Show what would be changed without making changes")
    args = parser.parse_args()
    
    success = main(dry_run=args.dry_run)
    sys.exit(0 if success else 1)
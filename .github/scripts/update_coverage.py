#!/usr/bin/env python
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

import argparse
import json
import logging
from pathlib import Path
from textwrap import dedent

log = logging.getLogger(__name__)

# Configuration
SCRIPT = Path(__file__)
SCRIPT_NAME = SCRIPT.stem
SCRIPT_DIR = SCRIPT.parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # Two levels up from .github/scripts/

# Input/Output files
COVERAGE_FILE = PROJECT_ROOT / "coverage.json"
README_FILE = PROJECT_ROOT / "README.md"
DOCS_INDEX_FILE = PROJECT_ROOT / "docs/index.md"
ALL_INPUTS = [COVERAGE_FILE]
ALL_OUTPUTS = [README_FILE, DOCS_INDEX_FILE]

# Constants
BADGE_MARKER = "<!-- coverage-badge -->"


def determine_coverage_color(coverage_pct: int) -> str:
    """Determine badge color based on coverage percentage.
    
    Args:
        coverage_pct: Coverage percentage as integer.
        
    Returns:
        Color name for badge.
    """
    if coverage_pct >= 90:
        return "brightgreen"
    elif coverage_pct >= 80:
        return "yellow"
    elif coverage_pct >= 70:
        return "orange"
    else:
        return "red"


def update_readme_badge(coverage_pct: int, dry_run: bool = False) -> None:
    """Update the coverage badge in README.md.
    
    Args:
        coverage_pct: Coverage percentage to display.
        dry_run: If True, don't write changes to file.
    """
    coverage_colour = determine_coverage_color(coverage_pct)
    coverage_svg_url = f"https://img.shields.io/badge/coverage-{coverage_pct}%25-{coverage_colour}.svg"
    badge_md = f'<img src="{coverage_svg_url}" alt="Coverage">'
    
    log.info(f"Coverage: {coverage_pct}% (color: {coverage_colour})")
    
    for output_file in ALL_OUTPUTS:
        update_markdown_file(output_file, badge_md, dry_run)


def update_markdown_file(output_file: Path, badge_md: str, dry_run: bool) -> None:
    markdown_content = output_file.read_text()
    
    first_marker_end, second_marker_start = get_badge_marker_positions(markdown_content, BADGE_MARKER)
    
    # Replace content between markers
    new_readme = (
        markdown_content[:first_marker_end] +
        f"    {badge_md}\n" +
        markdown_content[second_marker_start:]
    )
    
    if dry_run:
        log.info(f"DRY RUN: Would update {output_file.relative_to(PROJECT_ROOT)} with badge: {badge_md}")
    else:
        output_file.write_text(new_readme)
        log.info(f"Updated {output_file.relative_to(PROJECT_ROOT)} with coverage badge")

def get_badge_marker_positions(content: str, badge_marker: str) -> tuple[int, int]:
    """Get positions of badge markers in the content.
    
    Args:
        content: The markdown content as a string.
        
    Returns:
        A tuple with the end position of the first marker and the start position of the second marker.
        
    Raises:
        ValueError: If markers are not found or are in the wrong order.
    """
    first_marker = content.find(badge_marker)
    if first_marker == -1:
        raise ValueError(f"First badge marker '{badge_marker}' not found.")
    
    # Find the end of the first marker line
    first_marker_end = content.find('\n', first_marker) + 1
    
    # Find the second marker starting after the first one
    second_marker_pos = content.find(badge_marker, first_marker_end)
    if second_marker_pos == -1:
        raise ValueError(f"Second marker '{badge_marker}' not found")
    
    # Find the start of the second marker line (go back to beginning of line)
    second_marker_start = content.rfind('\n', 0, second_marker_pos) + 1

    return first_marker_end, second_marker_start


def main(dry_run: bool = False) -> None:
    """Main function to update coverage badge in README.
    
    Args:
        dry_run: If True, don't write changes to file.
    """
    # Check if coverage file exists
    if not COVERAGE_FILE.exists():
        log.error(f"Coverage file not found: {COVERAGE_FILE.relative_to(PROJECT_ROOT)}")
        raise FileNotFoundError(f"Coverage file not found: {COVERAGE_FILE}")
    
    # Read coverage data
    coverage_data = json.loads(COVERAGE_FILE.read_text())
    coverage_pct = int(coverage_data["totals"]["percent_covered_display"])
    
    # Update README badge
    update_readme_badge(coverage_pct, dry_run=dry_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(f"""
        {SCRIPT_NAME} - Update coverage badge in README.md based on coverage.json.
        
        This script reads the coverage percentage from coverage.json and updates
        the coverage badge between the <!-- coverage-badge --> markers in README.md.
        
        INPUTS:
        - {COVERAGE_FILE.relative_to(PROJECT_ROOT)}
        
        OUTPUTS:
        - {README_FILE.relative_to(PROJECT_ROOT)} (updated badge)
        """)
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Run script in quiet mode")
    parser.add_argument("-v", "--verbose", action="store_true", help="Run script in verbose mode")
    parser.add_argument("-n", "--dry-run", action="store_true", 
                       help="Run the script without making any output changes.")
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.ERROR if args.quiet else logging.INFO,
        format="%(asctime)s|%(name)s|%(levelname)s|%(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    try:
        main(dry_run=args.dry_run)
    except Exception as e:
        log.error(f"Error updating coverage badge: {e}")
        raise
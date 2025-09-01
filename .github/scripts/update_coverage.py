import json
from pathlib import Path

COVERAGE_FILE = Path(__file__).parent / ".." / ".." / "coverage.json"
README_FILE = Path(__file__).parent / ".." / ".." / "README.md"
BADGE_MARKER = "<!-- coverage-badge -->"
coverage_pct = int(json.loads(COVERAGE_FILE.read_text())["totals"]["percent_covered_display"])
coverage_colour = "green" # Default to green
# Determine badge color based on coverage
if coverage_pct >= 90:
    coverage_colour = "brightgreen"
elif coverage_pct >= 80:
    coverage_colour = "yellow"
elif coverage_pct >= 70:
    coverage_colour = "orange"
else:
    coverage_colour = "red"


coverage_svg_url = f"https://img.shields.io/badge/coverage-{coverage_pct}%25-{coverage_colour}.svg"
badge_md = f'<img src="{coverage_svg_url}" alt="Coverage">'

# Between the two BADGE_MARKERS, replace existing content with badge_md
readme_text = README_FILE.read_text()

# Find the positions of the two markers
first_marker_pos = readme_text.find(BADGE_MARKER)
if first_marker_pos == -1:
    raise ValueError(f"First marker '{BADGE_MARKER}' not found in README")

# Find the end of the first marker line
first_marker_end = readme_text.find('\n', first_marker_pos) + 1

# Find the second marker starting after the first one
second_marker_pos = readme_text.find(BADGE_MARKER, first_marker_end)
if second_marker_pos == -1:
    raise ValueError(f"Second marker '{BADGE_MARKER}' not found in README")

# Find the start of the second marker line (go back to beginning of line)
second_marker_start = readme_text.rfind('\n', 0, second_marker_pos) + 1

# Replace content between markers
new_readme = (
    readme_text[:first_marker_end] +
    f"    {badge_md}\n" +
    readme_text[second_marker_start:]
)

# Write back to file
README_FILE.write_text(new_readme)
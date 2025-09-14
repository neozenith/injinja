#!/usr/bin/env python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "subprocess-run",
# ]
# ///

"""Multi-version testing script for Python and Jinja2 combinations.

This script tests injinja against multiple Python and Jinja2 versions
to ensure compatibility across supported versions.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from shlex import split
from textwrap import dedent

SCRIPT = Path(__file__)
SCRIPT_NAME = SCRIPT.stem
SCRIPT_DIR = SCRIPT.parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent

# Testing matrix configuration
PYTHON_VERSIONS = ["3.12", "3.13"]
JINJA2_VERSIONS = ["3.0.0", "3.1.0", "3.1.6"]

# Command execution helper
_run = lambda cmd: subprocess.check_output(split(cmd), text=True).strip()  # noqa: E731


def run_command(cmd: str, cwd: Path = PROJECT_ROOT, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    return subprocess.run(split(cmd), cwd=cwd, capture_output=True, text=True, check=check)


def create_test_environment(python_version: str, jinja2_version: str, test_dir: Path) -> bool:
    """Create and configure a test environment for a specific Python/Jinja2 combination."""
    env_name = f"py{python_version.replace('.', '')}_jinja{jinja2_version.replace('.', '')}"
    env_path = test_dir / env_name
    
    print(f"\n{'='*60}")
    print(f"Testing Python {python_version} with Jinja2 {jinja2_version}")
    print(f"Environment: {env_name}")
    print(f"{'='*60}")
    
    try:
        # Create virtual environment with specific Python version
        result = run_command(f"uv venv {env_path} --python {python_version}")
        if result.returncode != 0:
            print(f"Failed to create venv: {result.stderr}")
            return False
        
        # Install specific Jinja2 version and dependencies
        result = run_command(f"uv pip install --venv {env_path} jinja2=={jinja2_version} PyYAML deepmerge jsonschema pydantic")
        if result.returncode != 0:
            print(f"Failed to install dependencies: {result.stderr}")
            return False
        
        # Install current project in development mode
        result = run_command(f"uv pip install --venv {env_path} -e .")
        if result.returncode != 0:
            print(f"Failed to install project: {result.stderr}")
            return False
        
        # Install test dependencies
        result = run_command(f"uv pip install --venv {env_path} pytest pytest-cov")
        if result.returncode != 0:
            print(f"Failed to install test dependencies: {result.stderr}")
            return False
        
        # Run tests
        python_exe = env_path / "bin" / "python" if (env_path / "bin").exists() else env_path / "Scripts" / "python.exe"
        result = run_command(f"{python_exe} -m pytest tests/ -v")
        if result.returncode != 0:
            print(f"Tests failed: {result.stderr}")
            return False
        
        print(f"✅ Python {python_version} + Jinja2 {jinja2_version}: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Python {python_version} + Jinja2 {jinja2_version}: ERROR - {e}")
        return False


def main(clean: bool = False, dry_run: bool = False, python_versions: list[str] = None, jinja2_versions: list[str] = None):
    """Run multi-version testing."""
    test_dir = PROJECT_ROOT / "tmp" / "test_matrix"
    
    if clean and test_dir.exists():
        print(f"Cleaning up test directory: {test_dir}")
        if not dry_run:
            import shutil
            shutil.rmtree(test_dir)
    
    if not dry_run:
        test_dir.mkdir(parents=True, exist_ok=True)
    
    # Use provided versions or defaults
    python_vers = python_versions or PYTHON_VERSIONS
    jinja2_vers = jinja2_versions or JINJA2_VERSIONS
    
    print(f"Testing {len(python_vers)} Python versions × {len(jinja2_vers)} Jinja2 versions = {len(python_vers) * len(jinja2_vers)} combinations")
    
    if dry_run:
        print("DRY RUN: Would test the following combinations:")
        for py_ver in python_vers:
            for jinja_ver in jinja2_vers:
                print(f"  - Python {py_ver} + Jinja2 {jinja_ver}")
        return
    
    results = []
    for py_ver in python_vers:
        for jinja_ver in jinja2_vers:
            success = create_test_environment(py_ver, jinja_ver, test_dir)
            results.append((py_ver, jinja_ver, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST MATRIX SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, _, success in results if success)
    total = len(results)
    
    for py_ver, jinja_ver, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"Python {py_ver} + Jinja2 {jinja_ver}: {status}")
    
    print(f"\nOverall: {passed}/{total} combinations passed")
    
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=dedent(f"""\
        {SCRIPT_NAME} - Test injinja against multiple Python and Jinja2 versions.
        
        This script creates isolated environments for each Python/Jinja2 combination
        and runs the full test suite to ensure compatibility.
        
        Default testing matrix:
        - Python versions: {', '.join(PYTHON_VERSIONS)}
        - Jinja2 versions: {', '.join(JINJA2_VERSIONS)}
        
        Total combinations: {len(PYTHON_VERSIONS)} × {len(JINJA2_VERSIONS)} = {len(PYTHON_VERSIONS) * len(JINJA2_VERSIONS)}
        """)
    )
    parser.add_argument("-n", "--dry-run", action="store_true", help="Show what would be tested without running")
    parser.add_argument("--clean", action="store_true", help="Clean up test environments before running")
    parser.add_argument("--python-versions", nargs="+", help="Python versions to test (e.g., 3.12 3.13)")
    parser.add_argument("--jinja2-versions", nargs="+", help="Jinja2 versions to test (e.g., 3.0.0 3.1.6)")
    args = parser.parse_args()
    
    main(
        clean=args.clean,
        dry_run=args.dry_run,
        python_versions=args.python_versions,
        jinja2_versions=args.jinja2_versions
    )
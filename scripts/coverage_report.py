#!/usr/bin/env python3
"""
Script to generate and display code coverage for the IndigoBot test suite.
"""

import os
import re
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Dict, List, Tuple


def run_coverage():
    """Run pytest with coverage and generate reports."""
    print("Running tests with coverage analysis...")

    # Make sure we're in the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Run pytest with coverage
    cmd = [
        "python",
        "-m",
        "pytest",
        "--cov=src/indigobot",
        "--cov-report=term",
        "--cov-report=html:coverage_html",
        "--cov-report=xml:coverage.xml",
        "tests/",
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)

        # Parse coverage data
        coverage_data = parse_coverage_output(result.stdout)

        # Display coverage summary
        display_coverage_summary(coverage_data)

        # Identify files with low coverage
        low_coverage_files = identify_low_coverage_files(coverage_data)
        if low_coverage_files:
            print("\nFiles with low coverage (<70%):")
            for file_name, coverage in low_coverage_files:
                print(f"  - {file_name}: {coverage}%")

            print("\nSuggestions for improving coverage:")
            for file_name, _ in low_coverage_files:
                suggest_coverage_improvements(file_name)

        # Open the HTML report in a browser
        html_report = project_root / "coverage_html" / "index.html"
        if html_report.exists():
            print(f"\nOpening HTML report: {html_report}")
            webbrowser.open(f"file://{html_report}")
        else:
            print("\nHTML report was not generated.")

    except subprocess.CalledProcessError as e:
        print(f"Error running coverage: {e}")
        print(e.stdout)
        print(e.stderr)
        return 1

    return 0


def parse_coverage_output(output: str) -> Dict[str, Dict[str, int]]:
    """Parse the coverage output to extract file coverage data.

    :param output: The output from pytest-cov
    :type output: str
    :return: Dictionary mapping file names to coverage data
    :rtype: Dict[str, Dict[str, int]]
    """
    coverage_data = {}

    # Find the coverage section
    coverage_section = re.search(
        r"---------- coverage:.*?(\n.*?)+?TOTAL", output, re.MULTILINE
    )
    if not coverage_section:
        return coverage_data

    # Extract file data
    lines = coverage_section.group(0).split("\n")
    for line in lines:
        # Skip header and separator lines
        if not line or "---" in line or "TOTAL" in line or "coverage:" in line:
            continue

        # Parse file data
        parts = line.split()
        if len(parts) >= 4:
            file_name = parts[0]
            stmts = int(parts[1])
            miss = int(parts[2])
            cover = int(parts[3].rstrip("%"))

            coverage_data[file_name] = {"stmts": stmts, "miss": miss, "cover": cover}

    return coverage_data


def display_coverage_summary(coverage_data: Dict[str, Dict[str, int]]) -> None:
    """Display a summary of the coverage data.

    :param coverage_data: Dictionary mapping file names to coverage data
    :type coverage_data: Dict[str, Dict[str, int]]
    :return: None
    """
    if not coverage_data:
        print("\nNo coverage data found.")
        return

    total_stmts = sum(data["stmts"] for data in coverage_data.values())
    total_miss = sum(data["miss"] for data in coverage_data.values())

    if total_stmts > 0:
        total_cover = 100 - (total_miss * 100 / total_stmts)
    else:
        total_cover = 0

    print(f"\nOverall Coverage: {total_cover:.1f}%")
    print(f"Total Statements: {total_stmts}")
    print(f"Missed Statements: {total_miss}")


def identify_low_coverage_files(
    coverage_data: Dict[str, Dict[str, int]], threshold: int = 70
) -> List[Tuple[str, int]]:
    """Identify files with coverage below the threshold.

    :param coverage_data: Dictionary mapping file names to coverage data
    :type coverage_data: Dict[str, Dict[str, int]]
    :param threshold: Coverage threshold percentage
    :type threshold: int
    :return: List of tuples containing file name and coverage percentage
    :rtype: List[Tuple[str, int]]
    """
    low_coverage = []

    for file_name, data in coverage_data.items():
        if data["cover"] < threshold:
            low_coverage.append((file_name, data["cover"]))

    # Sort by coverage (ascending)
    low_coverage.sort(key=lambda x: x[1])

    return low_coverage


def suggest_coverage_improvements(file_name: str) -> None:
    """Suggest ways to improve coverage for a specific file.

    :param file_name: Name of the file
    :type file_name: str
    :return: None
    """
    base_name = os.path.basename(file_name)

    if "__main__" in file_name:
        print(f"  - {file_name}: Create tests for command-line interface functionality")
        print(f"    - Test argument parsing")
        print(f"    - Test different run modes (API, loader, interactive)")
        print(f"    - Test error handling")
    elif "quick_api" in file_name:
        print(f"  - {file_name}: Add tests for API endpoints and error handling")
        print(f"    - Test webhook endpoint with various payloads")
        print(f"    - Test rate limiting functionality")
        print(f"    - Test error handling in message processing")
    elif "places_tool" in file_name:
        print(
            f"  - {file_name}: Test tool functionality with various inputs and edge cases"
        )
        print(f"    - Test place lookup with different query types")
        print(f"    - Test handling of API errors")
        print(f"    - Test time-dependent functions with mocked datetime")
    else:
        print(
            f"  - {file_name}: Review untested functions and add appropriate test cases"
        )


if __name__ == "__main__":
    sys.exit(run_coverage())

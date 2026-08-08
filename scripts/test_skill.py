#!/usr/bin/env python3
"""
Test script to validate the SEC Company Report Generator skill components.
"""

import sys
import json
from pathlib import Path

# Add scripts to path
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from resolve_company import CompanyResolver, CompanyInfo

def test_company_resolution():
    """Test company resolution for various inputs."""
    resolver = CompanyResolver()

    test_cases = [
        ("MDT", "0001613103", "Medtronic plc"),
        ("AAPL", "0000320193", "Apple Inc."),
        ("JNJ", "0000200406", "Johnson & Johnson"),
        ("TSLA", "0001318605", "Tesla, Inc."),
        ("BRK.B", "0001067983", "Berkshire Hathaway Inc."),
        ("0001613103", "0001613103", "Medtronic plc"),
        ("1613103", "0001613103", "Medtronic plc"),
        ("Medtronic", "0001613103", "Medtronic plc"),
        ("Apple", "0000320193", "Apple Inc."),
    ]

    print("Testing Company Resolution...")
    all_passed = True

    for query, expected_cik, expected_name in test_cases:
        result = resolver.resolve(query)
        if result:
            cik_match = result.cik == expected_cik
            name_match = expected_name.lower() in result.name.lower()
            status = "[OK]" if cik_match and name_match else "[FAIL]"
            if not (cik_match and name_match):
                all_passed = False
            print(f"  {status} {query:20s} -> CIK: {result.cik:10s} | Ticker: {result.ticker:6s} | Name: {result.name}")
        else:
            print(f"  [FAIL] {query:20s} -> NOT FOUND")
            all_passed = False

    return all_passed


def test_imports():
    """Test that all modules can be imported."""
    print("\nTesting Imports...")

    modules = [
        "resolve_company",
        "fetch_10k",
        "enrich_data",
        "generate_report",
        "generate_report_main",
    ]

    all_passed = True
    for module in modules:
        try:
            __import__(module)
            print(f"  [OK] {module}")
        except Exception as e:
            print(f"  [FAIL] {module}: {e}")
            all_passed = False

    return all_passed


def test_scripts_exist():
    """Test that all script files exist."""
    print("\nTesting Script Files...")

    scripts = [
        "resolve_company.py",
        "fetch_10k.py",
        "enrich_data.py",
        "generate_report.py",
        "generate_report_main.py",
    ]

    all_passed = True
    for script in scripts:
        path = SCRIPTS_DIR / script
        if path.exists():
            print(f"  [OK] {script}")
        else:
            print(f"  [FAIL] {script} - NOT FOUND")
            all_passed = False

    return all_passed


def main():
    print("=" * 60)
    print("SEC Company Report Generator - Skill Validation")
    print("=" * 60)

    results = []
    results.append(("Script Files", test_scripts_exist()))
    results.append(("Imports", test_imports()))
    results.append(("Company Resolution", test_company_resolution()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n[OK] All validation tests passed!")
        return 0
    else:
        print("\n[FAIL] Some validation tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
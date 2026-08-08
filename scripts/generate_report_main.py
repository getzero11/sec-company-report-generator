#!/usr/bin/env python3
"""
Main Orchestrator for SEC Company Report Generator
Coordinates the full pipeline: resolve -> fetch 10-K -> enrich -> generate report
"""

import json
import sys
import os
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

SCRIPTS_DIR = Path(__file__).parent


def run_script(script_name: str, args: list, cwd: Path = None) -> Dict:
    """Run a Python script and return parsed JSON output."""
    script_path = SCRIPTS_DIR / script_name
    cmd = [sys.executable, str(script_path)] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=cwd)
        if result.returncode != 0:
            return {"error": result.stderr, "returncode": result.returncode}
        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        return {"error": f"Script {script_name} timed out"}
    except json.JSONDecodeError:
        return {"error": f"Script {script_name} returned non-JSON output", "stdout": result.stdout[:500]}
    except Exception as e:
        return {"error": str(e)}


def resolve_company(query: str, fmp_key: str = None) -> Dict:
    """Resolve company identifier to CIK, ticker, name."""
    args = [query]
    if fmp_key:
        args.extend(["--fmp-key", fmp_key])
    return run_script("resolve_company.py", args)


def fetch_10k(cik: str, output_file: str = None) -> Dict:
    """Fetch and parse latest 10-K filing."""
    args = [cik]
    if output_file:
        args.extend(["--output", output_file])
    return run_script("fetch_10k.py", args)


def enrich_data(ticker: str, company_name: str, cik: str,
                fmp_key: str = None, news_key: str = None,
                output_file: str = None) -> Dict:
    """Enrich with external data sources."""
    args = [ticker, company_name, cik]
    if fmp_key:
        args.extend(["--fmp-key", fmp_key])
    if news_key:
        args.extend(["--news-key", news_key])
    if output_file:
        args.extend(["--output", output_file])
    return run_script("enrich_data.py", args)


def generate_report(parsed_10k_file: str, enriched_file: str, output_file: str = None) -> Dict:
    """Generate final markdown report."""
    args = [parsed_10k_file, enriched_file]
    if output_file:
        args.extend(["--output", output_file])
    return run_script("generate_report.py", args)


def generate_docx(markdown_file: str, docx_file: str, company_name: str, ticker: str,
                  filing_date: str, report_date: str, cik: str) -> Dict:
    """Generate DOCX report from markdown."""
    args = [markdown_file, docx_file, company_name, ticker, filing_date, report_date, cik]
    return run_script("markdown_to_docx.py", args)


def main():
    parser = argparse.ArgumentParser(description="Generate SEC 10-K Company Report")
    parser.add_argument("query", help="Company ticker, name, or CIK (e.g., MDT, Medtronic, 0001613103)")
    parser.add_argument("--fmp-key", help="Financial Modeling Prep API key")
    parser.add_argument("--news-key", help="News API key")
    parser.add_argument("--output", help="Output report file path (default: <ticker>_10k_report.md)")
    parser.add_argument("--work-dir", help="Working directory for intermediate files")
    parser.add_argument("--skip-enrich", action="store_true", help="Skip external data enrichment")
    parser.add_argument("--keep-intermediate", action="store_true", help="Keep intermediate JSON files")
    parser.add_argument("--no-docx", action="store_true", help="Skip DOCX generation")

    args = parser.parse_args()

    # Setup working directory
    work_dir = Path(args.work_dir) if args.work_dir else Path.cwd() / "sec_report_work"
    work_dir.mkdir(parents=True, exist_ok=True)

    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        # Will use ticker after resolution
        output_file = work_dir / "report.md"

    print(f"[SEARCH] Resolving company: {args.query}")
    company = resolve_company(args.query, args.fmp_key)

    if "error" in company:
        print(f"[FAIL] Failed to resolve company: {company['error']}", file=sys.stderr)
        sys.exit(1)

    cik = company["cik"]
    ticker = company["ticker"]
    name = company["name"]

    print(f"[OK] Resolved: {name} ({ticker}) - CIK: {cik}")

    if not args.output:
        output_file = work_dir / f"{ticker}_10k_report.md"

    # Step 1: Fetch 10-K
    print(f"[DOC] Fetching latest 10-K for CIK {cik}...")
    parsed_10k_file = work_dir / f"{ticker}_10k_parsed.json"
    parsed_10k = fetch_10k(cik, str(parsed_10k_file))

    if "error" in parsed_10k:
        print(f"[FAIL] Failed to fetch 10-K: {parsed_10k['error']}", file=sys.stderr)
        sys.exit(1)

    filing_info = parsed_10k.get("filing_info", {})
    filing_date = filing_info.get("filing_date", "Unknown")
    report_date = filing_info.get("report_date", "Unknown")
    print(f"[OK] Fetched 10-K filed {filing_date}")

    # Step 2: Enrich data (optional)
    enriched_file = work_dir / f"{ticker}_enriched.json"
    if not args.skip_enrich:
        print(f"[SCIENCE] Enriching data from Yahoo Finance, FMP, News, Clinical Trials...")
        enriched = enrich_data(ticker, name, cik, args.fmp_key, args.news_key, str(enriched_file))

        if "error" in enriched:
            print(f"[WARN] Enrichment had errors: {enriched['error']}", file=sys.stderr)
            # Continue with empty enrichment
            enriched = {"metadata": {"ticker": ticker, "company_name": name, "cik": cik}}
    else:
        print("[SKIP] Skipping enrichment")
        enriched = {"metadata": {"ticker": ticker, "company_name": name, "cik": cik}}

    # Save enrichment if not already saved
    if not enriched_file.exists():
        with open(enriched_file, 'w') as f:
            json.dump(enriched, f, indent=2)

    # Step 3: Generate markdown report
    print(f"[WRITE] Generating markdown report...")
    result = generate_report(str(parsed_10k_file), str(enriched_file), str(output_file))

    if "error" in result:
        print(f"[FAIL] Failed to generate report: {result['error']}", file=sys.stderr)
        sys.exit(1)

    print(f"[OK] Markdown report generated: {output_file}")

    # Step 4: Generate DOCX report
    if not args.no_docx:
        docx_file = output_file.with_suffix('.docx')
        print(f"[WRITE] Generating DOCX report...")
        docx_result = generate_docx(str(output_file), str(docx_file), name, ticker, filing_date, report_date, cik)

        if "error" in docx_result:
            print(f"[WARN] DOCX generation had issues: {docx_result['error']}", file=sys.stderr)
        else:
            print(f"[OK] DOCX report generated: {docx_file}")

    # Cleanup intermediate files unless requested to keep
    if not args.keep_intermediate:
        for f in [parsed_10k_file, enriched_file]:
            if f.exists():
                f.unlink()

    print(f"\n[CHART] Report complete!")
    print(f"  Markdown: {output_file}")
    if not args.no_docx:
        print(f"  DOCX:     {output_file.with_suffix('.docx')}")


if __name__ == "__main__":
    main()
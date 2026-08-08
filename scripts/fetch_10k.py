#!/usr/bin/env python3
"""
10-K Filing Fetcher and Parser
Fetches the latest 10-K from SEC EDGAR and extracts all major sections.
"""

import json
import re
import sys
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

@dataclass
class FilingInfo:
    accession_number: str
    filing_date: str
    report_date: str
    form_type: str
    primary_document: str
    filing_url: str
    document_url: str

@dataclass
class SectionContent:
    section_id: str
    title: str
    content: str
    html_content: str = ""
    subsections: List['SectionContent'] = field(default_factory=list)

@dataclass
class Parsed10K:
    company_info: Dict
    filing_info: FilingInfo
    sections: Dict[str, SectionContent]
    financial_tables: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

class SECEdgarFetcher:
    BASE_URL = "https://www.sec.gov"
    EDGAR_SEARCH_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
    SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

    def __init__(self, user_agent: str = "SEC-Report-Generator/1.0 (contact@example.com)"):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.rate_limit_delay = 0.1  # 10 requests per second max per SEC guidelines

    def _rate_limit(self):
        time.sleep(self.rate_limit_delay)

    def get_company_submissions(self, cik: str) -> Dict:
        """Get all submissions for a company from SEC EDGAR."""
        self._rate_limit()
        url = self.SUBMISSIONS_URL.format(cik=cik.zfill(10))
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    def find_latest_10k(self, cik: str) -> Optional[FilingInfo]:
        """Find the latest 10-K filing for a company."""
        submissions = self.get_company_submissions(cik)

        # Look in recent filings first
        recent = submissions.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accession_numbers = recent.get("accessionNumber", [])
        filing_dates = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        primary_documents = recent.get("primaryDocument", [])

        for i, form in enumerate(forms):
            if form == "10-K":
                accession = accession_numbers[i].replace("-", "")
                filing_date = filing_dates[i]
                report_date = report_dates[i] if i < len(report_dates) else filing_date
                primary_doc = primary_documents[i] if i < len(primary_documents) else ""

                filing_url = f"{self.BASE_URL}/Archives/edgar/data/{int(cik)}/{accession}/"
                doc_url = f"{filing_url}{primary_doc}" if primary_doc else filing_url

                return FilingInfo(
                    accession_number=accession_numbers[i],
                    filing_date=filing_date,
                    report_date=report_date,
                    form_type="10-K",
                    primary_document=primary_doc,
                    filing_url=filing_url,
                    document_url=doc_url
                )

        # Check older filings if not in recent
        for filing_file in submissions.get("filings", {}).get("files", []):
            self._rate_limit()
            resp = self.session.get(f"{self.BASE_URL}{filing_file['name']}", timeout=30)
            resp.raise_for_status()
            older = resp.json()
            forms = older.get("form", [])
            accession_numbers = older.get("accessionNumber", [])
            filing_dates = older.get("filingDate", [])
            report_dates = older.get("reportDate", [])
            primary_documents = older.get("primaryDocument", [])

            for i, form in enumerate(forms):
                if form == "10-K":
                    accession = accession_numbers[i].replace("-", "")
                    filing_date = filing_dates[i]
                    report_date = report_dates[i] if i < len(report_dates) else filing_date
                    primary_doc = primary_documents[i] if i < len(primary_documents) else ""

                    filing_url = f"{self.BASE_URL}/Archives/edgar/data/{int(cik)}/{accession}/"
                    doc_url = f"{filing_url}{primary_doc}" if primary_doc else filing_url

                    return FilingInfo(
                        accession_number=accession_numbers[i],
                        filing_date=filing_date,
                        report_date=report_date,
                        form_type="10-K",
                        primary_document=primary_doc,
                        filing_url=filing_url,
                        document_url=doc_url
                    )

        return None

    def fetch_filing_html(self, filing_info: FilingInfo) -> str:
        """Fetch the HTML content of the 10-K filing."""
        self._rate_limit()
        response = self.session.get(filing_info.document_url, timeout=60)
        response.raise_for_status()
        return response.text

    def fetch_filing_index(self, filing_info: FilingInfo) -> List[Dict]:
        """Fetch the filing index to get all documents."""
        self._rate_limit()
        index_url = f"{filing_info.filing_url}index.json"
        response = self.session.get(index_url, timeout=30)
        if response.status_code == 200:
            return response.json().get("directory", {}).get("item", [])
        return []

class TenKParser:
    """Parse 10-K HTML into structured sections."""

    # Major 10-K section patterns
    SECTION_PATTERNS = {
        # Part I
        "item1": (r"ITEM\s+1[.\s]*BUSINESS", "Business"),
        "item1a": (r"ITEM\s+1A[.\s]*RISK\s+FACTORS", "Risk Factors"),
        "item1b": (r"ITEM\s+1B[.\s]*UNRESOLVED\s+STAFF\s+COMMENTS", "Unresolved Staff Comments"),
        "item2": (r"ITEM\s+2[.\s]*PROPERTIES", "Properties"),
        "item3": (r"ITEM\s+3[.\s]*LEGAL\s+PROCEEDINGS", "Legal Proceedings"),
        "item4": (r"ITEM\s+4[.\s]*MINE\s+SAFETY\s+DISCLOSURES", "Mine Safety Disclosures"),
        # Part II
        "item5": (r"ITEM\s+5[.\s]*MARKET\s+FOR\s+REGISTRANT", "Market for Registrant's Common Equity"),
        "item6": (r"ITEM\s+6[.\s]*SELECTED\s+FINANCIAL\s+DATA", "Selected Financial Data"),
        "item7": (r"ITEM\s+7[.\s]*MANAGEMENT", "Management's Discussion and Analysis"),
        "item7a": (r"ITEM\s+7A[.\s]*QUANTITATIVE\s+AND\s+QUALITATIVE", "Quantitative and Qualitative Disclosures"),
        "item8": (r"ITEM\s+8[.\s]*FINANCIAL\s+STATEMENTS", "Financial Statements and Supplementary Data"),
        "item9": (r"ITEM\s+9[.\s]*CHANGES\s+IN\s+AND\s+DISAGREEMENTS", "Changes in and Disagreements with Accountants"),
        "item9a": (r"ITEM\s+9A[.\s]*CONTROLS\s+AND\s+PROCEDURES", "Controls and Procedures"),
        "item9b": (r"ITEM\s+9B[.\s]*OTHER\s+INFORMATION", "Other Information"),
        "item9c": (r"ITEM\s+9C[.\s]*DISCLOSURE\s+REGARDING\s+FOREIGN", "Disclosure Regarding Foreign Jurisdictions"),
        # Part III
        "item10": (r"ITEM\s+10[.\s]*DIRECTORS", "Directors, Executive Officers and Corporate Governance"),
        "item11": (r"ITEM\s+11[.\s]*EXECUTIVE\s+COMPENSATION", "Executive Compensation"),
        "item12": (r"ITEM\s+12[.\s]*SECURITY\s+OWNERSHIP", "Security Ownership of Certain Beneficial Owners and Management"),
        "item13": (r"ITEM\s+13[.\s]*CERTAIN\s+RELATIONSHIPS", "Certain Relationships and Related Transactions"),
        "item14": (r"ITEM\s+14[.\s]*PRINCIPAL\s+ACCOUNTANT", "Principal Accountant Fees and Services"),
        # Part IV
        "item15": (r"ITEM\s+15[.\s]*EXHIBITS", "Exhibits and Financial Statement Schedules"),
        "item16": (r"ITEM\s+16[.\s]*FORM\s+10-K\s+SUMMARY", "Form 10-K Summary"),
    }

    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, 'html.parser')
        self.text = self.soup.get_text(separator='\n', strip=True)
        self.sections: Dict[str, SectionContent] = {}

    def parse(self) -> Dict[str, SectionContent]:
        """Parse the 10-K into sections."""
        # Find all section boundaries
        boundaries = self._find_section_boundaries()

        # Extract content for each section
        for i, (section_id, (start_pos, title)) in enumerate(boundaries):
            end_pos = boundaries[i + 1][1][0] if i + 1 < len(boundaries) else len(self.text)
            content = self.text[start_pos:end_pos].strip()

            # Also get HTML content
            html_content = self._get_html_for_range(start_pos, end_pos)

            self.sections[section_id] = SectionContent(
                section_id=section_id,
                title=title,
                content=content,
                html_content=html_content
            )

        # Parse financial tables
        self._parse_financial_tables()

        return self.sections

    def _find_section_boundaries(self) -> List[Tuple[int, Tuple[int, str]]]:
        """Find the start positions of each major section."""
        boundaries = []

        for section_id, (pattern, title) in self.SECTION_PATTERNS.items():
            matches = list(re.finditer(pattern, self.text, re.IGNORECASE))
            if matches:
                # Use the first match (usually the main section, not TOC)
                start_pos = matches[0].start()
                boundaries.append((section_id, (start_pos, title)))

        # Sort by position in document
        boundaries.sort(key=lambda x: x[1][0])
        return boundaries

    def _get_html_for_range(self, start: int, end: int) -> str:
        """Extract HTML content corresponding to a text range."""
        # This is approximate - we find elements that contain text from this range
        # For simplicity, return the full HTML (could be optimized)
        return str(self.soup)

    def _parse_financial_tables(self):
        """Extract financial statement tables from the filing."""
        tables = self.soup.find_all('table')
        financial_tables = []

        for table in tables:
            # Check if this looks like a financial table
            text = table.get_text(strip=True).lower()
            financial_keywords = ['revenue', 'net income', 'assets', 'liabilities', 'equity',
                                  'cash flow', 'earnings per share', 'consolidated']
            if any(kw in text for kw in financial_keywords):
                rows = []
                for tr in table.find_all('tr'):
                    cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                    if cells:
                        rows.append(cells)
                if rows:
                    financial_tables.append({
                        'html': str(table),
                        'rows': rows,
                        'text_preview': text[:500]
                    })

        self.financial_tables = financial_tables


def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_10k.py <CIK> [--output <file>]", file=sys.stderr)
        sys.exit(1)

    cik = sys.argv[1]
    output_file = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]

    fetcher = SECEdgarFetcher()
    print(f"Fetching submissions for CIK {cik}...", file=sys.stderr)

    filing_info = fetcher.find_latest_10k(cik)
    if not filing_info:
        print(f"No 10-K found for CIK {cik}", file=sys.stderr)
        sys.exit(1)

    print(f"Found 10-K: {filing_info.filing_date} (Report: {filing_info.report_date})", file=sys.stderr)
    print(f"Fetching document from {filing_info.document_url}...", file=sys.stderr)

    html = fetcher.fetch_filing_html(filing_info)
    print(f"Fetched {len(html)} characters", file=sys.stderr)

    parser = TenKParser(html)
    sections = parser.parse()

    result = Parsed10K(
        company_info={"cik": cik},
        filing_info=filing_info,
        sections=sections,
        financial_tables=parser.financial_tables,
        metadata={
            "parsed_at": datetime.now().isoformat(),
            "total_sections": len(sections),
            "total_financial_tables": len(parser.financial_tables)
        }
    )

    # Convert to serializable dict
    output = {
        "company_info": result.company_info,
        "filing_info": asdict(result.filing_info),
        "sections": {k: asdict(v) for k, v in result.sections.items()},
        "financial_tables": result.financial_tables,
        "metadata": result.metadata
    }

    if output_file:
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Saved to {output_file}", file=sys.stderr)
        # Also print minimal success JSON to stdout for script chaining
        print(json.dumps({"success": True, "output_file": output_file, "filing_date": filing_info.filing_date}))
    else:
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
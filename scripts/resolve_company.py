#!/usr/bin/env python3
"""
Company Resolution Script
Resolves company identifiers (ticker, name, CIK) to standardized company info.
"""

import json
import re
import sys
import requests
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class CompanyInfo:
    cik: str
    ticker: str
    name: str
    exchange: str
    sic: str = ""
    sector: str = ""
    industry: str = ""

# Fallback data for common companies when SEC API is unavailable
FALLBACK_COMPANIES = {
    "MDT": {"cik": "0001613103", "ticker": "MDT", "name": "Medtronic plc", "exchange": "NYSE", "sector": "Healthcare", "industry": "Medical Devices"},
    "AAPL": {"cik": "0000320193", "ticker": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "sector": "Technology", "industry": "Consumer Electronics"},
    "JNJ": {"cik": "0000200406", "ticker": "JNJ", "name": "Johnson & Johnson", "exchange": "NYSE", "sector": "Healthcare", "industry": "Pharmaceuticals"},
    "TSLA": {"cik": "0001318605", "ticker": "TSLA", "name": "Tesla, Inc.", "exchange": "NASDAQ", "sector": "Automotive", "industry": "Electric Vehicles"},
    "BRK.B": {"cik": "0001067983", "ticker": "BRK.B", "name": "Berkshire Hathaway Inc.", "exchange": "NYSE", "sector": "Financial Services", "industry": "Conglomerate"},
    "BRK-A": {"cik": "0001067983", "ticker": "BRK-A", "name": "Berkshire Hathaway Inc.", "exchange": "NYSE", "sector": "Financial Services", "industry": "Conglomerate"},
    "MSFT": {"cik": "0000789019", "ticker": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ", "sector": "Technology", "industry": "Software"},
    "GOOGL": {"cik": "0001652044", "ticker": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ", "sector": "Technology", "industry": "Internet Services"},
    "GOOG": {"cik": "0001652044", "ticker": "GOOG", "name": "Alphabet Inc.", "exchange": "NASDAQ", "sector": "Technology", "industry": "Internet Services"},
    "AMZN": {"cik": "0001018724", "ticker": "AMZN", "name": "Amazon.com, Inc.", "exchange": "NASDAQ", "sector": "Consumer Cyclical", "industry": "E-Commerce"},
    "META": {"cik": "0001326801", "ticker": "META", "name": "Meta Platforms, Inc.", "exchange": "NASDAQ", "sector": "Technology", "industry": "Social Media"},
    "NVDA": {"cik": "0001045810", "ticker": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ", "sector": "Technology", "industry": "Semiconductors"},
    "UNH": {"cik": "0000731766", "ticker": "UNH", "name": "UnitedHealth Group Inc.", "exchange": "NYSE", "sector": "Healthcare", "industry": "Healthcare Plans"},
    "V": {"cik": "0001403161", "ticker": "V", "name": "Visa Inc.", "exchange": "NYSE", "sector": "Financial Services", "industry": "Credit Services"},
    "JPM": {"cik": "0000019617", "ticker": "JPM", "name": "JPMorgan Chase & Co.", "exchange": "NYSE", "sector": "Financial Services", "industry": "Banks"},
    "WMT": {"cik": "0000104169", "ticker": "WMT", "name": "Walmart Inc.", "exchange": "NYSE", "sector": "Consumer Defensive", "industry": "Discount Stores"},
    "PG": {"cik": "0000080424", "ticker": "PG", "name": "Procter & Gamble Co.", "exchange": "NYSE", "sector": "Consumer Defensive", "industry": "Household Products"},
}

class CompanyResolver:
    def __init__(self):
        self.sec_company_tickers_url = "https://www.sec.gov/files/company_tickers.json"
        self.sec_company_tickers_exchange_url = "https://www.sec.gov/files/company_tickers_exchange.json"
        self._cik_cache: Dict[str, CompanyInfo] = {}
        self._ticker_cache: Dict[str, CompanyInfo] = {}
        self._name_cache: Dict[str, CompanyInfo] = {}
        self._sec_data_loaded = False

    def _load_sec_tickers(self) -> Dict:
        """Load SEC company tickers mapping."""
        try:
            headers = {"User-Agent": "SEC-Report-Generator/1.0 (contact@example.com)"}
            response = requests.get(self.sec_company_tickers_url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            # SEC format: {"0": {"cik_str": 1613103, "ticker": "MDT", "title": "Medtronic plc"}, ...}
            return {str(v["cik_str"]).zfill(10): v for v in data.values()}
        except Exception as e:
            print(f"Warning: Could not load SEC tickers: {e}", file=sys.stderr)
            return {}

    def _load_sec_tickers_exchange(self) -> Dict:
        """Load SEC company tickers with exchange info."""
        try:
            headers = {"User-Agent": "SEC-Report-Generator/1.0 (contact@example.com)"}
            response = requests.get(self.sec_company_tickers_exchange_url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            # SEC format: {"data": [[cik, name, ticker, exchange], ...]}
            return {str(row[0]).zfill(10): {"cik": str(row[0]).zfill(10), "name": row[1], "ticker": row[2], "exchange": row[3]}
                    for row in data.get("data", [])}
        except Exception as e:
            print(f"Warning: Could not load SEC tickers exchange: {e}", file=sys.stderr)
            return {}

    def _load_fallback_data(self):
        """Load fallback company data when SEC API is unavailable."""
        for ticker, info in FALLBACK_COMPANIES.items():
            company = CompanyInfo(
                cik=info["cik"],
                ticker=info["ticker"],
                name=info["name"],
                exchange=info["exchange"],
                sector=info.get("sector", ""),
                industry=info.get("industry", "")
            )
            self._cik_cache[company.cik] = company
            self._ticker_cache[company.ticker.upper()] = company
            self._name_cache[company.name.lower()] = company
            # Also index by partial name
            words = company.name.lower().split()
            for word in words:
                if len(word) > 3 and word not in self._name_cache:
                    self._name_cache[word] = company

    def _build_caches(self):
        """Build lookup caches from SEC data."""
        if self._cik_cache:
            return

        # Try SEC first
        tickers = self._load_sec_tickers()
        tickers_exchange = self._load_sec_tickers_exchange()

        if tickers:
            self._sec_data_loaded = True
            # Merge data
            for cik, info in tickers.items():
                exchange_info = tickers_exchange.get(cik, {})
                company = CompanyInfo(
                    cik=cik,
                    ticker=info.get("ticker", ""),
                    name=info.get("title", ""),
                    exchange=exchange_info.get("exchange", ""),
                )
                self._cik_cache[cik] = company
                if company.ticker:
                    self._ticker_cache[company.ticker.upper()] = company
                if company.name:
                    self._name_cache[company.name.lower()] = company
                    # Also index by partial name
                    words = company.name.lower().split()
                    for word in words:
                        if len(word) > 3 and word not in self._name_cache:
                            self._name_cache[word] = company

        # Always load fallback data to fill gaps
        print("Loading fallback company data", file=sys.stderr)
        self._load_fallback_data()

    def resolve(self, query: str) -> Optional[CompanyInfo]:
        """
        Resolve a query to CompanyInfo.
        Query can be: CIK (with or without leading zeros), ticker, or company name.
        """
        self._build_caches()
        query = query.strip()

        # Try CIK (numeric, possibly with leading zeros)
        if query.isdigit():
            cik = query.zfill(10)
            if cik in self._cik_cache:
                return self._cik_cache[cik]
            # Try without leading zeros
            cik_no_zeros = query.lstrip('0').zfill(10)
            if cik_no_zeros in self._cik_cache:
                return self._cik_cache[cik_no_zeros]

        # Try ticker (uppercase)
        ticker_upper = query.upper()
        if ticker_upper in self._ticker_cache:
            return self._ticker_cache[ticker_upper]

        # Try exact name match (case insensitive)
        name_lower = query.lower()
        if name_lower in self._name_cache:
            return self._name_cache[name_lower]

        # Try partial name match
        for key, company in self._name_cache.items():
            if name_lower in key or key in name_lower:
                return company

        return None

    def resolve_with_fmp(self, query: str, api_key: str = None) -> Optional[CompanyInfo]:
        """
        Fallback resolution using FMP API if available.
        """
        if not api_key:
            return self.resolve(query)

        try:
            # FMP search endpoint
            url = f"https://financialmodelingprep.com/api/v3/search"
            params = {"query": query, "limit": 10, "apikey": api_key}
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            results = response.json()

            for result in results:
                # Match by symbol, name, or CIK
                if (result.get("symbol", "").upper() == query.upper() or
                    result.get("name", "").lower() == query.lower() or
                    str(result.get("cik", "")).zfill(10) == query.zfill(10)):
                    return CompanyInfo(
                        cik=str(result.get("cik", "")).zfill(10),
                        ticker=result.get("symbol", ""),
                        name=result.get("name", ""),
                        exchange=result.get("exchange", ""),
                        sector=result.get("sector", ""),
                        industry=result.get("industry", "")
                    )
        except Exception as e:
            print(f"FMP resolution failed: {e}", file=sys.stderr)

        return self.resolve(query)


def main():
    if len(sys.argv) < 2:
        print("Usage: python resolve_company.py <ticker|name|CIK> [--fmp-key <key>]", file=sys.stderr)
        sys.exit(1)

    query = sys.argv[1]
    fmp_key = None
    if "--fmp-key" in sys.argv:
        idx = sys.argv.index("--fmp-key")
        if idx + 1 < len(sys.argv):
            fmp_key = sys.argv[idx + 1]

    resolver = CompanyResolver()
    company = resolver.resolve_with_fmp(query, fmp_key)

    if company:
        print(json.dumps(asdict(company), indent=2))
    else:
        print(f"Error: Could not resolve company: {query}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
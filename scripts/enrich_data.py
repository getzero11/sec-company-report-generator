#!/usr/bin/env python3
"""
Data Enrichment Script
Fetches supplemental data from Yahoo Finance, FMP, news, clinical trials, and regulatory sources.
"""

import json
import sys
import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# Try to import MCP tools - these would be available in the Claude environment
try:
    # These are placeholders - actual MCP calls would be made via the Claude tool system
    pass
except ImportError:
    pass


@dataclass
class YahooFinanceData:
    quote: Dict = field(default_factory=dict)
    summary: Dict = field(default_factory=dict)
    chart: Dict = field(default_factory=dict)
    key_statistics: Dict = field(default_factory=dict)
    financial_data: Dict = field(default_factory=dict)
    major_holders: Dict = field(default_factory=dict)
    insider_transactions: Dict = field(default_factory=dict)
    analyst_estimates: Dict = field(default_factory=dict)
    earnings_history: Dict = field(default_factory=dict)
    revenue_history: List[Dict] = field(default_factory=list)
    error: str = ""

@dataclass
class FMPData:
    profile: Dict = field(default_factory=dict)
    income_statement: List[Dict] = field(default_factory=list)
    balance_sheet: List[Dict] = field(default_factory=list)
    cash_flow: List[Dict] = field(default_factory=list)
    ratios: List[Dict] = field(default_factory=list)
    dcf: Dict = field(default_factory=dict)
    enterprise_value: List[Dict] = field(default_factory=list)
    analyst_estimates: List[Dict] = field(default_factory=list)
    earnings_surprises: List[Dict] = field(default_factory=list)
    sec_filings: List[Dict] = field(default_factory=list)
    insider_trading: List[Dict] = field(default_factory=list)
    institutional_holders: List[Dict] = field(default_factory=list)
    error: str = ""

@dataclass
class NewsData:
    articles: List[Dict] = field(default_factory=list)
    press_releases: List[Dict] = field(default_factory=list)
    analyst_ratings: List[Dict] = field(default_factory=list)
    error: str = ""

@dataclass
class ClinicalData:
    trials: List[Dict] = field(default_factory=list)
    fda_actions: List[Dict] = field(default_factory=list)
    error: str = ""

@dataclass
class EnrichedData:
    yahoo_finance: YahooFinanceData = field(default_factory=YahooFinanceData)
    fmp: FMPData = field(default_factory=FMPData)
    news: NewsData = field(default_factory=NewsData)
    clinical: ClinicalData = field(default_factory=ClinicalData)
    metadata: Dict = field(default_factory=dict)


class YahooFinanceFetcher:
    """Fetch data from Yahoo Finance."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = "https://query1.finance.yahoo.com/v10/finance"
        self.base_url_v8 = "https://query1.finance.yahoo.com/v8/finance"

    def fetch_quote(self, ticker: str) -> Dict:
        url = f"{self.base_url}/quoteSummary/{ticker}"
        params = {"modules": "price,summaryDetail,defaultKeyStatistics,financialData,assetProfile"}
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json().get("quoteSummary", {}).get("result", [{}])[0]
        except Exception as e:
            return {"error": str(e)}

    def fetch_chart(self, ticker: str, period: str = "1y") -> Dict:
        url = f"{self.base_url_v8}/chart/{ticker}"
        params = {"period1": int((datetime.now() - timedelta(days=365)).timestamp()),
                  "period2": int(datetime.now().timestamp()),
                  "interval": "1d"}
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json().get("chart", {}).get("result", [{}])[0]
        except Exception as e:
            return {"error": str(e)}

    def fetch_all(self, ticker: str) -> YahooFinanceData:
        data = YahooFinanceData()
        try:
            quote_data = self.fetch_quote(ticker)
            data.quote = quote_data.get("price", {})
            data.summary = quote_data.get("summaryDetail", {})
            data.key_statistics = quote_data.get("defaultKeyStatistics", {})
            data.financial_data = quote_data.get("financialData", {})
            data.asset_profile = quote_data.get("assetProfile", {})
        except Exception as e:
            data.error = str(e)

        try:
            data.chart = self.fetch_chart(ticker)
        except Exception as e:
            data.error = data.error or str(e)

        return data


class FMPFetcher:
    """Fetch data from Financial Modeling Prep."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("FMP_API_KEY")
        self.base_url = "https://financialmodelingprep.com/api/v3"

    def _get(self, endpoint: str, params: Dict = None) -> Any:
        if not self.api_key:
            return {"error": "FMP_API_KEY not set"}
        if params is None:
            params = {}
        params["apikey"] = self.api_key
        try:
            resp = requests.get(f"{self.base_url}/{endpoint}", params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def fetch_profile(self, ticker: str) -> Dict:
        return self._get(f"profile/{ticker}")

    def fetch_income_statement(self, ticker: str, period: str = "annual", limit: int = 5) -> List[Dict]:
        return self._get(f"income-statement/{ticker}", {"period": period, "limit": limit})

    def fetch_balance_sheet(self, ticker: str, period: str = "annual", limit: int = 5) -> List[Dict]:
        return self._get(f"balance-sheet-statement/{ticker}", {"period": period, "limit": limit})

    def fetch_cash_flow(self, ticker: str, period: str = "annual", limit: int = 5) -> List[Dict]:
        return self._get(f"cash-flow-statement/{ticker}", {"period": period, "limit": limit})

    def fetch_ratios(self, ticker: str, period: str = "annual", limit: int = 5) -> List[Dict]:
        return self._get(f"ratios/{ticker}", {"period": period, "limit": limit})

    def fetch_dcf(self, ticker: str) -> Dict:
        return self._get(f"discounted-cash-flow/{ticker}")

    def fetch_enterprise_value(self, ticker: str, limit: int = 5) -> List[Dict]:
        return self._get(f"enterprise-values/{ticker}", {"limit": limit})

    def fetch_analyst_estimates(self, ticker: str, period: str = "annual", limit: int = 5) -> List[Dict]:
        return self._get(f"analyst-estimates/{ticker}", {"period": period, "limit": limit})

    def fetch_earnings_surprises(self, ticker: str, limit: int = 10) -> List[Dict]:
        return self._get(f"earnings-surprises/{ticker}", {"limit": limit})

    def fetch_sec_filings(self, ticker: str, limit: int = 20) -> List[Dict]:
        return self._get(f"sec-filings/{ticker}", {"limit": limit})

    def fetch_insider_trading(self, ticker: str, limit: int = 50) -> List[Dict]:
        return self._get(f"insider-trading/{ticker}", {"limit": limit})

    def fetch_institutional_holders(self, ticker: str) -> List[Dict]:
        return self._get(f"institutional-holder/{ticker}")

    def fetch_all(self, ticker: str) -> FMPData:
        data = FMPData()
        if not self.api_key:
            data.error = "FMP_API_KEY not configured"
            return data

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(self.fetch_profile, ticker): "profile",
                executor.submit(self.fetch_income_statement, ticker): "income_statement",
                executor.submit(self.fetch_balance_sheet, ticker): "balance_sheet",
                executor.submit(self.fetch_cash_flow, ticker): "cash_flow",
                executor.submit(self.fetch_ratios, ticker): "ratios",
                executor.submit(self.fetch_dcf, ticker): "dcf",
                executor.submit(self.fetch_enterprise_value, ticker): "enterprise_value",
                executor.submit(self.fetch_analyst_estimates, ticker): "analyst_estimates",
                executor.submit(self.fetch_earnings_surprises, ticker): "earnings_surprises",
                executor.submit(self.fetch_sec_filings, ticker): "sec_filings",
                executor.submit(self.fetch_insider_trading, ticker): "insider_trading",
                executor.submit(self.fetch_institutional_holders, ticker): "institutional_holders",
            }

            for future in as_completed(futures):
                key = futures[future]
                try:
                    result = future.result()
                    if isinstance(result, dict) and "error" in result:
                        data.error = data.error or result["error"]
                    else:
                        setattr(data, key, result)
                except Exception as e:
                    data.error = data.error or str(e)

        return data


class NewsFetcher:
    """Fetch recent news and press releases."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2"

    def fetch_company_news(self, ticker: str, company_name: str, days: int = 30) -> List[Dict]:
        if not self.api_key:
            return []
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        params = {
            "q": f"{ticker} OR {company_name}",
            "from": from_date,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": 50,
            "apiKey": self.api_key
        }
        try:
            resp = requests.get(f"{self.base_url}/everything", params=params, timeout=30)
            resp.raise_for_status()
            return resp.json().get("articles", [])
        except Exception as e:
            return [{"error": str(e)}]

    def fetch_press_releases(self, ticker: str, days: int = 30) -> List[Dict]:
        # Could use PR Newswire, Business Wire APIs, or SEC EDGAR 8-K filings
        # For now, return empty - would need specific API access
        return []

    def fetch_all(self, ticker: str, company_name: str) -> NewsData:
        data = NewsData()
        data.articles = self.fetch_company_news(ticker, company_name)
        data.press_releases = self.fetch_press_releases(ticker)
        return data


class ClinicalTrialsFetcher:
    """Fetch clinical trials data from ClinicalTrials.gov."""

    def __init__(self):
        self.base_url = "https://clinicaltrials.gov/api/v2"

    def fetch_trials(self, company_name: str, conditions: List[str] = None) -> List[Dict]:
        # Search by sponsor/collaborator
        params = {
            "query.term": company_name,
            "filter.overallStatus": "Recruiting,Active not recruiting,Enrolling by invitation,Completed",
            "pageSize": 100,
            "format": "json"
        }
        try:
            resp = requests.get(f"{self.base_url}/studies", params=params, timeout=30)
            resp.raise_for_status()
            studies = resp.json().get("studies", [])
            return [self._parse_study(s) for s in studies]
        except Exception as e:
            return [{"error": str(e)}]

    def _parse_study(self, study: Dict) -> Dict:
        protocol = study.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        status = protocol.get("statusModule", {})
        design = protocol.get("designModule", {})
        conditions = protocol.get("conditionsModule", {})
        interventions = protocol.get("interventionsModule", {})
        locations = protocol.get("locationsModule", {})

        return {
            "nct_id": identification.get("nctId", ""),
            "title": identification.get("briefTitle", ""),
            "phase": design.get("phases", []),
            "status": status.get("overallStatus", ""),
            "conditions": conditions.get("conditions", []),
            "interventions": [i.get("name", "") for i in interventions.get("interventions", [])],
            "start_date": status.get("startDateStruct", {}).get("date", ""),
            "completion_date": status.get("completionDateStruct", {}).get("date", ""),
            "enrollment": design.get("enrollmentInfo", {}).get("count", 0),
            "locations": [loc.get("facility", "") for loc in locations.get("locations", [])[:5]],
            "sponsor": identification.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name", "")
        }

    def fetch_fda_actions(self, company_name: str) -> List[Dict]:
        # FDA API for enforcement reports, recalls, approvals
        # Would need FDA openFDA API
        return []

    def fetch_all(self, company_name: str) -> ClinicalData:
        data = ClinicalData()
        data.trials = self.fetch_trials(company_name)
        data.fda_actions = self.fetch_fda_actions(company_name)
        return data


def enrich_company_data(ticker: str, company_name: str, cik: str,
                        fmp_key: str = None, news_key: str = None) -> EnrichedData:
    """Main enrichment function - fetches from all sources in parallel."""
    enriched = EnrichedData()
    enriched.metadata = {
        "ticker": ticker,
        "company_name": company_name,
        "cik": cik,
        "enriched_at": datetime.now().isoformat(),
        "sources": []
    }

    with ThreadPoolExecutor(max_workers=4) as executor:
        # Yahoo Finance (no API key needed for basic data)
        yahoo_future = executor.submit(YahooFinanceFetcher().fetch_all, ticker)

        # FMP (requires API key)
        fmp_future = executor.submit(FMPFetcher(fmp_key).fetch_all, ticker)

        # News (requires API key)
        news_future = executor.submit(NewsFetcher(news_key).fetch_all, ticker, company_name)

        # Clinical Trials (for healthcare companies)
        clinical_future = executor.submit(ClinicalTrialsFetcher().fetch_all, company_name)

        enriched.yahoo_finance = yahoo_future.result()
        enriched.fmp = fmp_future.result()
        enriched.news = news_future.result()
        enriched.clinical = clinical_future.result()

        # Track which sources succeeded
        if not enriched.yahoo_finance.error:
            enriched.metadata["sources"].append("yahoo_finance")
        if not enriched.fmp.error:
            enriched.metadata["sources"].append("fmp")
        if not enriched.news.error:
            enriched.metadata["sources"].append("news")
        if not enriched.clinical.error:
            enriched.metadata["sources"].append("clinical_trials")

    return enriched


def main():
    if len(sys.argv) < 3:
        print("Usage: python enrich_data.py <ticker> <company_name> [cik] [--fmp-key <key>] [--news-key <key>] [--output <file>]", file=sys.stderr)
        sys.exit(1)

    ticker = sys.argv[1]
    company_name = sys.argv[2]
    cik = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else ""

    fmp_key = None
    news_key = None
    output_file = None

    args = sys.argv[4:] if len(sys.argv) > 3 else sys.argv[3:]
    for i, arg in enumerate(args):
        if arg == "--fmp-key" and i + 1 < len(args):
            fmp_key = args[i + 1]
        elif arg == "--news-key" and i + 1 < len(args):
            news_key = args[i + 1]
        elif arg == "--output" and i + 1 < len(args):
            output_file = args[i + 1]

    print(f"Enriching data for {ticker} ({company_name})...", file=sys.stderr)
    enriched = enrich_company_data(ticker, company_name, cik, fmp_key, news_key)

    output = asdict(enriched)

    if output_file:
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"Saved to {output_file}", file=sys.stderr)
        # Also print minimal success JSON to stdout for script chaining
        print(json.dumps({"success": True, "output_file": output_file, "sources": enriched.metadata.get("sources", [])}))
    else:
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
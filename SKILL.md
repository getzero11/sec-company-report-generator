---
name: sec-company-report-generator
description: Generate comprehensive SEC company reports from latest 10-K filings. Use this skill whenever user requests company analysis, SEC filings review, financial reports, 10-K analysis, or needs a structured company report with financials, business overview, risk factors, MD&A, and supplemental data from Yahoo Finance, FMP, clinical trials, regulatory filings, and news. Trigger on: "company report", "10-K analysis", "SEC filing analysis", "financial report", "company analysis", "Medtronic report", "MDT analysis", or any company ticker/CIK request.
---

# SEC Company Report Generator

A skill for generating comprehensive company reports from SEC EDGAR 10-K filings enriched with multiple data sources.

## Overview

This skill fetches the latest 10-K filing from SEC EDGAR for any public company, extracts all major sections, and enriches the report with:
- Financial data (annual revenue current year + 2-3 prior years with % changes)
- Yahoo Finance data (key statistics, ratios, analyst estimates)
- FMP (Financial Modeling Prep) data (income statement, balance sheet, cash flow, ratios)
- Recent news and press releases
- Clinical trials data (for healthcare/biotech companies)
- Regulatory filings and FDA actions (for healthcare)
- Company website information

## Workflow

### 1. Input Resolution
- Accept company identifier: ticker symbol (e.g., "MDT"), company name ("Medtronic"), or CIK ("0001613103")
- Resolve to CIK using SEC EDGAR search or FMP/Yahoo Finance
- Validate the company exists and has 10-K filings

### 2. Fetch 10-K Filing
- Search SEC EDGAR for latest 10-K (form type "10-K") within the last year
- Primary URL pattern: `https://www.sec.gov/Archives/edgar/data/{CIK}/{accession-number}/{filing-name}.htm`
- Alternative: SEC EDGAR search API at `https://www.sec.gov/edgar/search/#/dateRange=1y&category=custom&ciks={CIK}&entityName={NAME}&forms=10-K`
- Download and parse the HTML filing

### 3. Extract 10-K Sections
Parse and extract ALL major sections:
- **Part I**: Business, Risk Factors, Unresolved Staff Comments, Properties, Legal Proceedings
- **Part II**: Market for Registrant's Common Equity, Selected Financial Data, MD&A, Quantitative/Qualitative Disclosures, Financial Statements, Changes in Accounting
- **Part III**: Directors/Executive Officers, Executive Compensation, Security Ownership, Certain Relationships, Principal Accountant Fees
- **Part IV**: Exhibits, Financial Statement Schedules
- **Financial Statements**: Income Statement, Balance Sheet, Cash Flow, Statement of Equity, Notes

### 4. Enrich with External Data Sources
Run in parallel:
- **Yahoo Finance**: Key stats, valuation, profitability, growth, analyst estimates, major holders
- **FMP**: Full financial statements (annual), ratios, DCF valuation, enterprise value
- **Google Search/News**: Recent news (last 30 days), press releases, analyst ratings changes
- **ClinicalTrials.gov**: Active/completed trials (for healthcare companies)
- **FDA/Regulatory**: Warning letters, approvals, recalls (for healthcare)
- **Company Website**: Investor presentations, earnings call transcripts, ESG reports

### 5. Generate Report
Create a comprehensive markdown report with:
- Executive Summary
- Business Overview (from Part I Item 1)
- Risk Factors Summary (top 10-15 from Part I Item 1A)
- Financial Highlights (revenue trend table with YoY % changes)
- MD&A Summary (key themes from Part II Item 7)
- Financial Statements Summary
- Valuation & Analyst Estimates
- Recent Developments & News
- Clinical/Regulatory Pipeline (if applicable)
- ESG & Sustainability Highlights
- Appendices: Full section references, data sources

## Data Sources & MCP Tools

### Primary Sources
- **SEC EDGAR**: `firecrawl_scrape` or `firecrawl_search` for 10-K HTML
- **Yahoo Finance**: `mcp__Yahoo_Finance__get_quote`, `mcp__Yahoo_Finance__quote_summary`, `mcp__Yahoo_Finance__get_chart`
- **FMP**: `mcp__FMP__company`, `mcp__FMP__statements`, `mcp__FMP__discountedCashFlow`, `mcp__FMP__analyst`
- **Web Search**: `mcp__Tinyfish_Search__search` + `mcp__Tinyfish_Search__fetch_content` for news
- **Clinical Trials**: `mcp__PubMed__search_articles` or direct ClinicalTrials.gov API
- **FDA**: Direct API or web search for regulatory actions

### MCP Server Setup
Required MCP servers (configure in settings.json):
- `firecrawl` - for SEC EDGAR scraping
- `tinyfish` - for web search and news
- `yahoo_finance` - for market data
- `fmp` - for financial statements and ratios
- `pubmed` - for clinical trials

## Report Structure Template

```markdown
# [Company Name] ([Ticker]) - SEC 10-K Analysis Report
**Filing Date:** [Date] | **Period End:** [Date] | **CIK:** [CIK]
**Report Generated:** [Current Date]

---

## Executive Summary
[2-3 paragraph synthesis of key investment thesis, financial health, and outlook]

---

## 1. Business Overview (Part I, Item 1)
[Company description, segments, products, markets, competitive position]
### 1.1 Reportable Segments
[Table: Segment | Revenue | % of Total | YoY Growth]
### 1.2 Geographic Breakdown
[Table: Region | Revenue | % of Total]
### 1.3 Key Products & Pipeline
[Major products, approval status, pipeline highlights]

---

## 2. Risk Factors Summary (Part I, Item 1A)
[Top 10-15 risk factors categorized by theme]
| # | Risk Factor | Category | Severity |
|---|-------------|----------|----------|

---

## 3. Financial Highlights
### 3.1 Revenue Trend (Last 4 Years)
| Fiscal Year | Revenue ($M) | YoY Change % | Net Income ($M) | EPS Diluted |
|-------------|--------------|--------------|-----------------|-------------|
| 202X        | X,XXX        | +X.X%        | XXX             | X.XX        |
| 202X-1      | X,XXX        | +X.X%        | XXX             | X.XX        |
| 202X-2      | X,XXX        | +X.X%        | XXX             | X.XX        |
| 202X-3      | X,XXX        | -            | XXX             | X.XX        |

### 3.2 Key Ratios (Latest Year)
| Metric | Value | Industry Avg | Trend |
|--------|-------|--------------|-------|
| Gross Margin | XX.X% | XX.X% | ↑/↓ |
| Operating Margin | XX.X% | XX.X% | ↑/↓ |
| Net Margin | XX.X% | XX.X% | ↑/↓ |
| ROE | XX.X% | XX.X% | ↑/↓ |
| ROIC | XX.X% | XX.X% | ↑/↓ |
| Debt/Equity | X.XX | X.XX | ↑/↓ |
| Current Ratio | X.XX | X.XX | ↑/↓ |
| Free Cash Flow Yield | X.X% | X.X% | ↑/↓ |

### 3.3 Balance Sheet Strength
[Cash, debt, working capital, key changes]

---

## 4. Management's Discussion & Analysis (Part II, Item 7)
### 4.1 Results of Operations
[Revenue drivers, segment performance, margin analysis]
### 4.2 Liquidity & Capital Resources
[Cash flow, debt maturity, share repurchases, dividends]
### 4.3 Critical Accounting Estimates
[Key estimates and judgments]
### 4.4 Forward-Looking Guidance
[Company outlook, if provided]

---

## 5. Financial Statements Summary (Part II, Item 8)
### 5.1 Income Statement Highlights
[Revenue, COGS, Gross Profit, OpEx, Operating Income, Net Income]
### 5.2 Balance Sheet Highlights
[Assets, Liabilities, Equity, key line items]
### 5.3 Cash Flow Highlights
[Operating, Investing, Financing cash flows]
### 5.4 Notable Footnotes
[Revenue recognition, acquisitions, debt, commitments, contingencies]

---

## 6. Valuation & Analyst Estimates
### 6.1 Current Valuation
| Metric | Value |
|--------|-------|
| Market Cap | $XXX.B |
| Enterprise Value | $XXX.B |
| P/E (TTM) | XX.X |
| P/E (Forward) | XX.X |
| EV/EBITDA | XX.X |
| P/S | X.XX |
| P/B | X.XX |

### 6.2 Analyst Estimates
| Period | Revenue Est. | EPS Est. | # Analysts |
|--------|--------------|----------|------------|
| FY 202X | $XXX.B | $X.XX | XX |
| FY 202X+1 | $XXX.B | $X.XX | XX |

### 6.3 DCF Valuation (FMP)
[Intrinsic value, assumptions, sensitivity]

---

## 7. Recent Developments & News (Last 30-90 Days)
[Recent earnings, acquisitions, partnerships, regulatory actions, clinical data]

---

## 8. Clinical & Regulatory Pipeline (Healthcare/Biotech Only)
### 8.1 Active Clinical Trials
| Trial ID | Phase | Indication | Status | Est. Completion |
|----------|-------|------------|--------|-----------------|
### 8.2 FDA Actions & Approvals
[Recent approvals, warning letters, recalls, PDUFA dates]

---

## 9. ESG & Sustainability
[Key ESG metrics, carbon footprint, diversity, governance highlights]

---

## 10. Ownership & Governance (Part III)
### 10.1 Major Shareholders
| Holder | Shares | % Outstanding | Change |
|--------|--------|---------------|--------|
### 10.2 Insider Transactions (Recent)
[Form 4 filings summary]
### 10.3 Board & Leadership
[Key directors, committee composition]

---

## Appendices
### A. Full 10-K Section Index
[Links to each major section in original filing]
### B. Data Sources & Methodology
[List of all sources, retrieval dates, any adjustments]
### C. Glossary
[Key terms and metrics definitions]
```

## Implementation Scripts

### `scripts/fetch_10k.py`
- Input: ticker/CIK/company name
- Output: parsed 10-K sections as JSON
- Uses: firecrawl for SEC EDGAR, handles pagination and HTML parsing

### `scripts/enrich_data.py`
- Input: company ticker/CIK
- Output: enriched financial data JSON from Yahoo, FMP, news, clinical trials
- Parallel fetches from all sources

### `scripts/generate_report.py`
- Input: parsed 10-K JSON + enriched data JSON
- Output: formatted markdown report
- Uses Jinja2 template matching the report structure above

### `scripts/resolve_company.py`
- Input: user query (ticker, name, CIK)
- Output: standardized company info (CIK, ticker, name, exchange)

## Usage Examples

### Example 1: By Ticker
```
User: "Generate a 10-K report for MDT"
→ Resolves to Medtronic plc (CIK: 0001613103, Ticker: MDT)
→ Fetches latest 10-K (filed April 2026 for FY2026)
→ Enriches with Yahoo, FMP, news, clinical trials
→ Outputs comprehensive report
```

### Example 2: By Company Name
```
User: "Analyze Johnson & Johnson's latest 10-K"
→ Resolves to JNJ (CIK: 0000200406)
→ Same workflow
```

### Example 3: By CIK
```
User: "Get SEC report for CIK 0001318605"
→ Resolves to Tesla (TSLA)
→ Same workflow
```

## Error Handling

- **No 10-K found**: Check for 10-K/A (amendment), 20-F (foreign issuers), or 40-F (Canadian)
- **Rate limited**: Implement exponential backoff, cache results
- **Parsing failures**: Fallback to raw text extraction, flag sections needing manual review
- **Missing financial data**: Note gaps, use prior year as proxy with clear disclosure
- **Healthcare-specific**: Only run clinical/FDA enrichment for relevant sectors (SIC codes 283x, 384x, 806x)

## Caching Strategy

- Cache 10-K HTML for 24 hours (filings don't change)
- Cache financial data for 4 hours (market data changes)
- Cache news for 1 hour
- Cache company resolution indefinitely

## Output Formats

- **Primary**: Markdown (.md) - human readable, version controllable
- **Secondary**: HTML (.html) - styled for browser viewing
- **Data**: JSON (.json) - structured data for further analysis
- **Optional**: PDF via pandoc/weasyprint

## Validation Checklist

Before delivering report, verify:
- [ ] Company identifier correctly resolved
- [ ] Latest 10-K filing date confirmed
- [ ] Revenue table has 4 years with YoY % changes
- [ ] All major 10-K sections represented
- [ ] Financial data matches 10-K numbers (cross-check)
- [ ] External data sources cited with retrieval dates
- [ ] Healthcare enrichment run for relevant companies
- [ ] Report renders correctly as markdown
- [ ] No placeholder text remains

## Testing

Test cases in `evals/evals.json`:
1. **MDT (Medtronic)** - Large cap healthcare, complex segments, clinical pipeline
2. **AAPL (Apple)** - Tech, simple segments, massive financials
3. **JNJ (Johnson & Johnson)** - Healthcare conglomerate, pharma + medtech + consumer
4. **TSLA (Tesla)** - Auto/energy, unique accounting, high volatility
5. **BRK.B (Berkshire)** - Conglomerate, insurance focus, unique structure

Each test validates: correct CIK resolution, 10-K fetch success, revenue table accuracy, section completeness, enrichment data presence.
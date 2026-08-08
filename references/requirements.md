# SEC Company Report Generator - Requirements

## Python Dependencies
```
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
jinja2>=3.1.0
python-dotenv>=1.0.0
python-docx>=1.1.0
```

## MCP Servers Required

Configure in `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "firecrawl": {
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"]
    },
    "tinyfish": {
      "command": "npx",
      "args": ["-y", "@tinyfish/search-mcp"]
    },
    "yahoo_finance": {
      "command": "npx",
      "args": ["-y", "@yahoo-finance/mcp"]
    },
    "fmp": {
      "command": "npx",
      "args": ["-y", "@fmp/mcp"],
      "env": {
        "FMP_API_KEY": "your_fmp_api_key"
      }
    },
    "pubmed": {
      "command": "npx",
      "args": ["-y", "@pubmed/mcp"]
    }
  }
}
```

## API Keys Needed

1. **FMP (Financial Modeling Prep)** - Required for detailed financials, ratios, DCF
   - Get at: https://financialmodelingprep.com/developer/docs
   - Free tier: 250 requests/day

2. **News API** - Optional, for recent news
   - Get at: https://newsapi.org/
   - Free tier: 100 requests/day

3. **Firecrawl** - For SEC EDGAR scraping (has free tier)
   - Get at: https://firecrawl.dev/

## Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or if using uv
uv pip install -r requirements.txt
```

## Usage

### Command Line
```bash
# By ticker
python scripts/generate_report_main.py MDT --fmp-key YOUR_FMP_KEY

# By company name
python scripts/generate_report_main.py "Medtronic" --fmp-key YOUR_FMP_KEY

# By CIK
python scripts/generate_report_main.py 0001613103 --fmp-key YOUR_FMP_KEY

# With custom output
python scripts/generate_report_main.py AAPL --output aapl_report.md --fmp-key YOUR_FMP_KEY

# Skip enrichment (faster, SEC data only)
python scripts/generate_report_main.py MSFT --skip-enrich

# Skip DOCX generation
python scripts/generate_report_main.py MDT --no-docx
```

### Via Skill (in Claude)
```
/skill sec-company-report-generator
Generate a 10-K report for MDT
```

## Output

The script generates a comprehensive report in **both .md and .docx formats**:

**Markdown (.md)** - Human readable, version controllable
**Word Document (.docx)** - Professional formatted with title page, TOC, styled tables

### Report Contents:
- **Executive Summary** - Key investment thesis, financial health, outlook
- **Business Overview (Item 1)** - Segments, products, markets, competitive position
- **Sales by Division/Geography** - Revenue by segment and region with YoY%
- **Risk Factors (Item 1A)** - Top 15 risks in categorized table
- **Financial Highlights** - **Annual Revenue (current + 3 prior years) with YoY% changes**
- **MD&A Summary (Item 7)** - Results, liquidity, accounting estimates, guidance
- **Financial Statements (Item 8)** - Income statement, balance sheet, cash flow highlights
- **Valuation & Analyst Estimates** - P/E, EV/EBITDA, DCF, revenue/EPS estimates
- **Recent News & Press Releases** - Last 30-90 days
- **Clinical Trials & FDA Actions** - For healthcare/biotech companies
- **ESG & Sustainability** - Key metrics and initiatives
- **Ownership & Governance (Part III)** - Major holders, insiders, board
- **Appendices** - Section index, data sources, glossary

## Architecture

```
scripts/
├── resolve_company.py      # CIK/Ticker/Name resolution
├── fetch_10k.py           # SEC EDGAR fetch + HTML parsing
├── enrich_data.py         # Yahoo Finance, FMP, News, Clinical Trials
├── generate_report.py     # Jinja2 template rendering (markdown)
├── markdown_to_docx.py    # Markdown to DOCX converter
└── generate_report_main.py # Main orchestrator
```

## Testing

```bash
# Run validation tests
python scripts/test_skill.py

# Test specific companies
python scripts/generate_report_main.py MDT --skip-enrich
python scripts/generate_report_main.py AAPL --skip-enrich
python scripts/generate_report_main.py JNJ --skip-enrich
```
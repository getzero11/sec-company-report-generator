# SEC Company Report Generator

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/getzero11/sec-company-report-generator)](https://github.com/getzero11/sec-company-report-generator/stargazers)

Generates comprehensive **SEC Form 10-K analysis reports** for any public company, enriched with financial data from Yahoo Finance & FMP, clinical trials, regulatory actions, news, and more. Outputs professional **Markdown (.md)** and **Word (.docx)** reports.

## 🚀 Features

| Feature | Description |
|---------|-------------|
| **SEC EDGAR 10-K Parsing** | Fetches latest 10-K filing directly from SEC EDGAR (HTML → structured sections) |
| **Multi-format Input** | Accepts ticker (MDT), company name (Medtronic), or CIK (0001613103) |
| **Financial Data** | Annual revenue (current + 3 prior years) with YoY% changes, key ratios, valuation metrics |
| **Segment & Geographic Revenue** | Sales breakdown by division/products and geography with growth rates |
| **Clinical Trials & FDA** | Active trials from ClinicalTrials.gov, FDA approvals/warnings (healthcare companies) |
| **Analyst Estimates** | Revenue/EPS consensus, target prices, DCF valuation from FMP |
| **Recent News & Press** | 30-90 day news from News API, earnings, regulatory actions |
| **Dual Output** | Markdown (version-controllable) + DOCX (professional with title page, TOC, styled tables) |
| **MCP Integration** | Works with firecrawl, tinyfish, yahoo_finance, fmp, pubmed MCP servers |

## 📦 Installation

```bash
git clone https://github.com/getzero11/sec-company-report-generator.git
cd sec-company-report-generator

# Install Python dependencies
pip install -r references/requirements.txt

# Or with uv
uv pip install -r references/requirements.txt
```

### Required API Keys

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| **FMP (Financial Modeling Prep)** | Financial statements, ratios, DCF, analyst estimates | 250 req/day |
| **News API** | Recent news & press releases | 100 req/day |
| **Firecrawl** | SEC EDGAR scraping (optional) | Free tier available |

Get keys at:
- FMP: https://financialmodelingprep.com/developer/docs
- News API: https://newsapi.org/
- Firecrawl: https://firecrawl.dev/

### MCP Server Setup (Optional)

Add to `~/.claude/settings.json` for enhanced data fetching:

```json
{
  "mcpServers": {
    "firecrawl": { "command": "npx", "args": ["-y", "firecrawl-mcp"] },
    "tinyfish": { "command": "npx", "args": ["-y", "@tinyfish/search-mcp"] },
    "yahoo_finance": { "command": "npx", "args": ["-y", "@yahoo-finance/mcp"] },
    "fmp": { 
      "command": "npx", 
      "args": ["-y", "@fmp/mcp"],
      "env": { "FMP_API_KEY": "your_key" }
    },
    "pubmed": { "command": "npx", "args": ["-y", "@pubmed/mcp"] }
  }
}
```

## 🎯 Usage

### Command Line

```bash
# By ticker symbol
python scripts/generate_report_main.py MDT --fmp-key YOUR_FMP_KEY

# By company name
python scripts/generate_report_main.py "Medtronic" --fmp-key YOUR_FMP_KEY

# By CIK
python scripts/generate_report_main.py 0001613103 --fmp-key YOUR_FMP_KEY

# Custom output path
python scripts/generate_report_main.py AAPL --output ./reports/aapl_report.md --fmp-key YOUR_KEY

# Skip enrichment (SEC data only, faster)
python scripts/generate_report_main.py MSFT --skip-enrich

# Skip DOCX generation
python scripts/generate_report_main.py MDT --no-docx --fmp-key YOUR_KEY
```

### Via Claude Skill

```
/skill sec-company-report-generator
Generate a 10-K report for MDT
```

## 📊 Report Contents

The generated report includes:

1. **Executive Summary** - Investment thesis, financial health, outlook
2. **Business Overview (Item 1)** - Segments, products, markets, competitive position
3. **Sales by Division & Geography** - Revenue tables with YoY% growth
4. **Risk Factors (Item 1A)** - Top 15 risks in categorized severity table
5. **Financial Highlights** - **4-year revenue trend with YoY%**, key ratios, balance sheet strength
6. **MD&A Summary (Item 7)** - Results, liquidity, accounting estimates, guidance
7. **Financial Statements (Item 8)** - Income statement, balance sheet, cash flow highlights
8. **Valuation & Analyst Estimates** - P/E, EV/EBITDA, DCF, revenue/EPS consensus
9. **Recent News & Press** - Last 30-90 days developments
10. **Clinical Trials & FDA Actions** - For healthcare/biotech companies
11. **ESG & Sustainability** - Key metrics and initiatives
12. **Ownership & Governance (Part III)** - Major holders, insiders, board
13. **Appendices** - Section index, data sources, glossary

## 📁 Project Structure

```
sec-company-report-generator/
├── SKILL.md                          # Skill definition for Claude
├── evals/evals.json                  # Test cases (MDT, AAPL, JNJ, TSLA, BRK.B)
├── references/requirements.md        # Dependencies, MCP config, usage docs
└── scripts/
    ├── resolve_company.py            # CIK/Ticker/Name resolution
    ├── fetch_10k.py                  # SEC EDGAR fetch + HTML parsing
    ├── enrich_data.py                # Yahoo Finance, FMP, News, Clinical Trials
    ├── generate_report.py            # Jinja2 markdown template rendering
    ├── markdown_to_docx.py           # Markdown → professional DOCX
    ├── generate_report_main.py       # CLI orchestrator
    └── test_skill.py                 # Validation tests
```

## ✅ Validation

```bash
# Run validation tests
python scripts/test_skill.py

# Expected output: All validation tests passed!
```

Test cases cover: MDT (healthcare), AAPL (tech), JNJ (healthcare conglomerate), TSLA (auto/energy), BRK.B (conglomerate)

## 📝 Example Output

**Markdown**: `MDT_10k_report.md` - Clean, version-controllable
**Word**: `MDT_10k_report.docx` - Professional formatting with:
- Title page (company name, ticker, filing dates)
- Table of Contents
- Styled tables with headers
- Section hierarchy

## 🔧 Configuration

Environment variables (or pass via CLI):

```bash
export FMP_API_KEY="your_fmp_key"
export NEWS_API_KEY="your_news_key"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure `python scripts/test_skill.py` passes
5. Submit a PR

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- SEC EDGAR for public filing access
- Financial Modeling Prep for financial data APIs
- Yahoo Finance for market data
- ClinicalTrials.gov for clinical trial data
- Firecrawl for web scraping infrastructure

---

**Repository**: https://github.com/getzero11/sec-company-report-generator  
**Issues**: https://github.com/getzero11/sec-company-report-generator/issues
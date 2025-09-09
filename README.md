# Financial Statement Analysis Pipeline for Banking Sector

A comprehensive, production-ready Python system for analyzing financial statements from banking sector PDFs. Features automated data extraction, quality assurance checks, vector embeddings for semantic search, and an interactive dashboard with AI-powered Q&A capabilities.

## 🚀 Features

### Core Functionality
- **PDF Ingestion & Parsing**: Extracts structured tables (Balance Sheet, Income Statement, Cash Flow) and unstructured text from annual reports
- **OCR Support**: Handles both native and scanned PDFs using OCR technology
- **Data Normalization**: Maps synonyms and standardizes financial data into canonical formats
- **Quality Assurance**: Automated checks for balance sheet equations, cash flow reconciliation, and financial anomalies
- **Vector Embeddings**: RAG-powered semantic search through financial notes using sentence-transformers and FAISS
- **Interactive Dashboard**: Streamlit-based interface with company selection, trends, and AI Q&A

### Unique Features
- **Financial Health Score (0-100)**: Proprietary scoring algorithm based on financial ratios and QA findings
- **Banking-Specific Analysis**: Tailored for financial institutions with relevant metrics and checks
- **Production Quality**: Error handling, logging, caching, and scalable architecture

## 📁 Project Structure

```
financial-analysis/
├── pipeline.py          # Main processing pipeline
├── dashboard.py         # Interactive Streamlit dashboard
├── utils.py             # Utility functions and calculations
├── pdf_parser.py        # PDF processing and data extraction
├── qa_checks.py         # Quality assurance and validation
├── embeddings.py        # Vector embeddings and semantic search
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── data/
    ├── pdfs/           # Input PDF files (create this directory)
    ├── output/         # Generated CSV files
    └── embeddings/     # FAISS index and metadata
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Installation Steps

1. **Clone or create the project directory**
```bash
mkdir financial-analysis
cd financial-analysis
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Create data directories**
```bash
mkdir -p data/pdfs data/output data/embeddings
```

4. **Add PDF files(optional)**
   - Place your financial statement PDFs in the `data/pdfs/` directory
   - Support formats: Annual reports, 10-K filings, financial statements
   - Naming convention: `CompanyName_Year.pdf` (e.g., `JPMorgan_2023.pdf`)

## 🚀 Usage
**Pipeline Options:**
- `--pdf-dir`: Directory containing PDF files (default: data/pdfs)
- `--output-dir`: Output directory for CSV files (default: data/output)
- `--embeddings-dir`: Directory for embeddings (default: data/embeddings)
- `--no-ocr`: Disable OCR for scanned PDFs
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Step 1: Launch the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will be available at `http://localhost:8501`

## 📊 Output Files

The pipeline generates the following files in `data/output/`:

### CSV Files
- **`income.csv`**: Income statement data with fields like revenue, net_income, operating_expenses
- **`balance.csv`**: Balance sheet data with assets, liabilities, equity
- **`cashflow.csv`**: Cash flow statement with operating, investing, financing activities
- **`notes.csv`**: Text chunks from notes and MD&A sections
- **`qa_findings.csv`**: Quality assurance findings with severity levels

### Embeddings
- **`notes.index`**: FAISS vector index for semantic search
- **`notes_meta.json`**: Metadata for text chunks

## 🎯 Dashboard Features

### 1. Overview Page
- Key financial metrics for selected company/year
- Revenue and asset trend charts
- Quick financial snapshot

### 2. Financial Trends
- Multi-year ratio analysis (ROA, ROE, Current Ratio, etc.)
- Interactive trend charts for any metric
- Comprehensive ratios table

### 3. QA Findings
- Automated quality checks results
- Severity-based filtering (Critical, Warning, Info)
- Detailed finding descriptions

### 4. RAG Q&A
- AI-powered question answering from financial notes
- Sample questions provided
- Company and year filtering
- Source document references

### 5. Health Score
- Proprietary Financial Health Score (0-100)
- Score component breakdown
- Historical trend analysis
- Strengths and concerns identification

## 🔧 Quality Assurance Checks

### Automated Validations
- **Balance Sheet Equation**: Assets = Liabilities + Equity
- **Net Income Consistency**: Tie-out with retained earnings changes
- **Cash Flow Reconciliation**: Statement vs balance sheet cash changes
- **Financial Anomalies**: Negative operating cash flow, low liquidity, interest coverage
- **Data Completeness**: Missing key financial fields

### Severity Levels
- **Critical**: Major accounting inconsistencies
- **Warning**: Potential red flags or unusual patterns
- **Info**: Missing data or informational notes

## 🤖 AI-Powered Q&A

### Sample Questions
- "What are the main risk factors for this company?"
- "How does the company manage liquidity risk?"
- "What are the company's revenue recognition policies?"
- "How has the company's debt structure changed?"

### RAG Technology
- Uses sentence-transformers for embeddings
- FAISS for efficient similarity search
- Context-aware answer generation
- Source document attribution

## 💯 Financial Health Score

### Scoring Components (0-100 scale)
- **Profitability (30%)**: ROA, operating margins
- **Liquidity (25%)**: Current ratio, cash ratios
- **Efficiency (20%)**: Asset turnover, operational metrics
- **Leverage (25%)**: Interest coverage, debt ratios

### Score Interpretation
- **80-100**: Excellent financial health
- **70-79**: Good financial position
- **50-69**: Fair, some concerns
- **0-49**: Poor, significant issues

## 📈 Supported Financial Metrics

### Income Statement
- Revenue, Sales, Turnover
- Cost of Revenue/Sales
- Gross Profit, Operating Income
- Interest Expense, Tax Expense
- Net Income, EPS

### Balance Sheet  
- Cash and Equivalents
- Accounts Receivable, Inventory
- Total Assets, Current Assets
- Accounts Payable, Current/Long-term Liabilities
- Shareholders' Equity, Retained Earnings

### Cash Flow
- Operating/Investing/Financing Activities
- Net Change in Cash
- Depreciation, Working Capital Changes

## 🔍 Advanced Features

### Field Mapping
Automatic synonym recognition maps various field names to canonical formats:
- "Revenue" = "Sales" = "Turnover" = "Net Sales"
- Handles banking-specific terminology
- Extensible mapping system

### Error Handling
- Graceful PDF parsing failures
- Missing data handling
- OCR fallback for scanned documents
- Comprehensive logging

### Scalability
- Batch processing for multiple PDFs
- Efficient memory usage
- Caching for dashboard performance
- Modular architecture

## 🛠️ Customization

### Adding New Financial Fields
1. Update `FIELD_MAPPINGS` in `utils.py`
2. Add synonyms for new fields
3. Update QA checks if needed

### Custom QA Rules
1. Extend `FinancialQAChecker` in `qa_checks.py`
2. Add new check methods
3. Define severity levels

### Dashboard Extensions
1. Add new pages in `dashboard.py`
2. Create custom visualizations
3. Extend health score calculations

## 🐛 Troubleshooting

### Common Issues

**"No PDF files found"**
- Ensure PDFs are in `data/pdfs/` directory
- Check file permissions

**"OCR failed"**
- Install tesseract: `sudo apt-get install tesseract-ocr` (Linux)
- Use `--no-ocr` flag to disable

**"Embeddings not loading"**
- Run pipeline first to generate embeddings
- Check `data/embeddings/` directory exists

**"Dashboard shows no data"**
- Verify CSV files exist in `data/output/`
- Check pipeline completed successfully

### Performance Optimization

**For large PDF batches:**
- Use `--no-ocr` if PDFs are text-based
- Process in smaller batches
- Monitor memory usage

**Dashboard performance:**
- Data is cached automatically
- Restart if data updates aren't reflected

## 📝 Logging

All operations are logged to `pipeline.log` with configurable levels:
- DEBUG: Detailed processing information
- INFO: General progress and results
- WARNING: Non-fatal issues
- ERROR: Processing failures

## 🤝 Contributing

This codebase is designed to be:
- **Modular**: Easy to extend with new features
- **Documented**: Comprehensive docstrings and comments
- **Tested**: Error handling and edge case management
- **Professional**: Production-ready code quality

## 📋 Requirements

See `requirements.txt` for complete dependency list. Key packages:
- pandas, numpy: Data processing
- pdfplumber, pytesseract: PDF parsing
- sentence-transformers, faiss: Embeddings
- streamlit, plotly: Dashboard and visualization

## 📄 License

This project is designed for professional financial analysis use. Ensure compliance with data privacy and financial regulations in your jurisdiction.

---

**Ready to analyze your financial statements? Start by placing PDF files in `data/pdfs/` and run `python pipeline.py`!**

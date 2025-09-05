# 📊 Financial Statement Analysis Dashboard

A comprehensive, full-stack application for analyzing financial statements from PDF reports. This intelligent system combines advanced PDF parsing, financial data extraction, and interactive visualization with real-time progress tracking and semantic search capabilities.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![React](https://img.shields.io/badge/react-18%2B-blue.svg)
![TypeScript](https://img.shields.io/badge/typescript-4.9%2B-blue.svg)

## 🌟 Key Features

### 📁 **Intelligent PDF Processing**
- **Multi-format Support**: Process both text-based and scanned PDFs with OCR
- **Real-time Progress Tracking**: Live progress bar (0-100%) with detailed status updates
- **Batch Processing**: Handle multiple financial documents simultaneously
- **Error Recovery**: Robust parsing with graceful handling of complex PDF structures

### 📈 **Advanced Financial Analysis**
- **Comprehensive Data Extraction**: Income statements, balance sheets, cash flow statements
- **Financial Ratio Calculation**: Automated computation of key financial ratios and metrics
- **Multi-year Trend Analysis**: Visualize financial performance over time
- **Quality Assurance**: Automated data validation and consistency checks

### 🎨 **Interactive Dashboard**
- **Modern UI**: Clean, responsive interface built with React and TypeScript
- **Dark/Light Mode**: Toggle between themes for comfortable viewing
- **Dynamic Visualizations**: Interactive charts and graphs for financial trends
- **Company Selection**: Easy navigation between multiple companies and years

### 🔍 **Semantic Search**
- **AI-Powered Search**: Find specific information in financial notes and MD&A sections
- **Vector Embeddings**: Advanced text similarity search using sentence transformers
- **Context-Aware Results**: Intelligent ranking of search results by relevance

### 🛡️ **Data Quality & Validation**
- **Automated QA Checks**: Built-in validation for financial data consistency
- **Error Detection**: Identify missing data, calculation errors, and anomalies
- **Data Normalization**: Standardize financial data across different reporting formats

## 🚀 Quick Start Guide

### Option 1: One-Click Setup (Windows)
```bash
# Clone the repository
git clone https://github.com/sujal-pawar/Financial_statement_analysis.git
cd Financial_statement_analysis

# Run the automated setup script
run_app.bat
```

The script will automatically:
1. ✅ Create Python virtual environment
2. ✅ Install all dependencies (Python + Node.js)
3. ✅ Start backend server on `http://localhost:5000`
4. ✅ Start frontend server on `http://localhost:5173`
5. ✅ Open application in your browser

### Option 2: Manual Setup

#### Prerequisites
- **Python 3.10+** ([Download](https://python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **Git** ([Download](https://git-scm.com/))

#### Backend Setup
```bash
# 1. Clone repository
git clone https://github.com/sujal-pawar/Financial_statement_analysis.git
cd Financial_statement_analysis

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install Python dependencies
pip install -r requirements.txt
```

#### Frontend Setup
```bash
# 1. Navigate to client directory
cd client

# 2. Install Node.js dependencies
npm install

# 3. Start development server
npm run dev
```

#### Start Backend Server
```bash
# In the main project directory
python server.py
```

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10, macOS 10.14, or Ubuntu 18.04+
- **RAM**: 4 GB (8 GB recommended for large PDFs)
- **Storage**: 2 GB free space
- **Internet**: Required for initial dependency installation

### Recommended Specifications
- **OS**: Windows 11, macOS 12+, or Ubuntu 20.04+
- **RAM**: 8 GB or more
- **CPU**: Multi-core processor for faster PDF processing
- **Storage**: SSD for better performance

## 🎯 How to Use the Application

### Step 1: Upload Financial Documents
1. **Open the application** at `http://localhost:5173`
2. **Click "Browse files"** or drag-and-drop PDF files
3. **Watch real-time progress** with detailed status updates:
   - 📄 File upload (0-10%)
   - 🔍 PDF parsing (10-45%)
   - 📊 Data extraction (45-75%)
   - ✅ Analysis completion (75-100%)

### Step 2: Explore Financial Data
1. **Select a company** from the dropdown menu
2. **Choose a year** to analyze
3. **Navigate through tabs**:
   - **📈 Overview**: Key financial metrics and summary
   - **📊 Financial Trends**: Multi-year comparison charts
   - **⚠️ QA Findings**: Data quality issues and recommendations
   - **🤖 Chatbot Assistant**: AI-powered financial insights

### Step 3: Advanced Analysis
1. **Use semantic search** to find specific information
2. **Compare financial ratios** across different periods
3. **Export data** for further analysis
4. **Review QA findings** for data validation

## 📄 Supported Document Types

### ✅ **Fully Supported**
- **SEC 10-K Filings**: Complete annual reports
- **Annual Reports**: Corporate annual financial reports
- **Quarterly Reports (10-Q)**: Interim financial statements
- **Proxy Statements**: When containing financial data
- **Financial Statements**: Standalone income statements, balance sheets, cash flow statements

### ⚠️ **Partially Supported**
- **Scanned PDFs**: Processed with OCR (may have lower accuracy)
- **Non-standard Formats**: Custom financial report layouts
- **International Reports**: Non-US GAAP reporting standards

### ❌ **Not Supported**
- **Encrypted/Secured PDFs**: Password-protected documents
- **Image-only Files**: Pure image files without text layer
- **Non-financial Documents**: General business documents without financial data

### 🔍 **Content Requirements**

For optimal results, PDFs should contain:
- **Tabular financial data** with clear row/column structure
- **Standard financial statement labels** (Revenue, Assets, Liabilities, etc.)
- **Numerical data** in recognizable formats ($, thousands, millions)
- **Company identification** information
- **Year/period** indicators

### 📝 **Recommended Test Files**

Try these types of documents for best results:
1. **Apple Inc. 10-K** - Clean, well-structured format
2. **Microsoft Annual Report** - Standard corporate reporting
3. **Amazon 10-Q** - Quarterly financial statements
4. **Google (Alphabet) 10-K** - Technology sector example

**Download Examples**: Visit SEC EDGAR database at `sec.gov/edgar` for official filings.

## 🔧 Configuration & Customization

### Environment Variables
```bash
# Backend Configuration
FLASK_ENV=development
UPLOAD_FOLDER=data/pdfs
OUTPUT_FOLDER=data/output
EMBEDDINGS_FOLDER=data/embeddings

# Frontend Configuration
VITE_API_URL=http://localhost:5000
VITE_APP_TITLE=Financial Analysis Dashboard
```

### Parser Settings
```python
# In server.py - Modify PDF parsing engine
parser_engine = 'pymupdf'  # Options: 'pymupdf', 'tesseract', 'tika'
```

### UI Customization
```typescript
// In client/src/App.tsx - Modify theme settings
const defaultTheme = 'light';  // Options: 'light', 'dark', 'auto'
```

## 🛠️ Troubleshooting Guide

### 🚨 **Common Issues & Solutions**

#### **"No companies available" Error**
**Symptoms**: Empty dropdown, no data after upload
**Solutions**:
1. ✅ Check if PDF contains recognizable financial tables
2. ✅ Verify file is not encrypted/password-protected
3. ✅ Try a standard SEC filing (10-K) for testing
4. ✅ Check browser console for detailed error messages

#### **Progress Bar Stuck/Freezing**
**Symptoms**: Progress bar stops updating, no completion
**Solutions**:
1. ✅ Check backend server logs for processing errors
2. ✅ Ensure sufficient RAM for large PDF files
3. ✅ Verify network connection for real-time updates
4. ✅ Refresh page and retry upload

#### **Backend Server Won't Start**
**Symptoms**: Connection refused, server startup errors
**Solutions**:
```bash
# Check port availability
netstat -an | grep :5000

# Verify Python environment
python --version  # Should be 3.10+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check detailed logs
tail -f api.log
```

#### **Frontend Build Errors**
**Symptoms**: White screen, compilation errors
**Solutions**:
```bash
# Clear cache and reinstall
cd client
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+

# Run development server
npm run dev
```

#### **PDF Processing Failures**
**Symptoms**: "Failed to process file" errors
**Solutions**:
1. ✅ Ensure PDF is not corrupted (`pdf can be opened manually`)
2. ✅ Try different parser engine in configuration
3. ✅ Check PDF has selectable text (not pure image)
4. ✅ Verify sufficient disk space for temporary files

#### **Semantic Search Not Working**
**Symptoms**: No search results, embeddings errors
**Solutions**:
1. ✅ Ensure PyTorch is properly installed
2. ✅ Check internet connection for model downloads
3. ✅ Verify sufficient RAM for embedding models
4. ✅ Check embeddings folder permissions

### 📋 **Log Files**
- **API Logs**: `api.log` - Backend server activities
- **Pipeline Logs**: `pipeline.log` - PDF processing details
- **Browser Console**: F12 → Console - Frontend errors
- **Network Tab**: F12 → Network - API communication issues

### 🔍 **Debug Mode**
```bash
# Enable verbose logging
export FLASK_ENV=development
export LOG_LEVEL=DEBUG

# Run with debug output
python server.py --debug
```

## 🏗️ Architecture & Technical Details

### 🔧 **Backend Stack**
- **Framework**: Flask (Python web framework)
- **PDF Processing**: PyMuPDF, Tesseract OCR, Apache Tika
- **Data Analysis**: Pandas, NumPy for financial calculations
- **AI/ML**: Sentence Transformers, FAISS for semantic search
- **Database**: JSON-based storage with CSV exports

### 🎨 **Frontend Stack**
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development and building
- **Styling**: Tailwind CSS for responsive design
- **Icons**: Lucide React for modern iconography
- **State Management**: React Context API

### 📁 **Project Structure**
```
Financial_statement_analysis/
├── 📁 client/                    # Frontend React application
│   ├── 📁 src/
│   │   ├── 📁 components/        # Reusable UI components
│   │   ├── 📁 context/           # State management
│   │   ├── 📁 services/          # API communication
│   │   └── 📁 types/             # TypeScript definitions
│   ├── 📄 package.json           # Node.js dependencies
│   └── 📄 vite.config.ts         # Build configuration
├── 📁 data/                      # Data storage directory
│   ├── 📁 pdfs/                  # Uploaded PDF files
│   ├── 📁 output/                # Processed financial data
│   └── 📁 embeddings/            # AI search embeddings
├── 📁 npnonlyf/                  # Backend processing modules
│   ├── 📄 pdf_parser.py          # PDF extraction logic
│   ├── 📄 pipeline.py            # Main processing pipeline
│   ├── 📄 embeddings.py          # Semantic search engine
│   ├── 📄 qa_checks.py           # Data validation
│   └── 📄 requirements.txt       # Python dependencies
├── 📄 server.py                  # Flask API server
├── 📄 run_app.bat               # Automated setup script
└── 📄 README.md                 # This documentation
```

### 🔄 **Data Flow**
1. **Upload**: PDF files uploaded via REST API
2. **Processing**: Background pipeline extracts financial data
3. **Storage**: Structured data saved as CSV and JSON
4. **Analysis**: Financial ratios and trends calculated
5. **Search**: Text embeddings created for semantic search
6. **Visualization**: Frontend displays interactive charts

### 🔒 **Security Features**
- **File Validation**: Only PDF files accepted
- **Size Limits**: Configurable upload size restrictions
- **CORS Protection**: Proper cross-origin request handling
- **Input Sanitization**: All user inputs validated and sanitized

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### 🐛 **Reporting Issues**
1. Check existing issues first
2. Provide detailed error messages and logs
3. Include system information and steps to reproduce
4. Attach sample PDF files (if not confidential)

### 💡 **Suggesting Features**
1. Describe the use case and benefits
2. Provide implementation suggestions
3. Consider backward compatibility
4. Include mockups or examples if applicable

### 🔧 **Development Setup**
```bash
# Fork the repository
git fork https://github.com/sujal-pawar/Financial_statement_analysis.git

# Clone your fork
git clone https://github.com/YOUR_USERNAME/Financial_statement_analysis.git

# Create feature branch
git checkout -b feature/your-feature-name

# Install development dependencies
pip install -r requirements-dev.txt
npm install --include=dev

# Make changes and test
python -m pytest tests/
npm test

# Submit pull request
git push origin feature/your-feature-name
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PyMuPDF** for excellent PDF processing capabilities
- **React Community** for comprehensive frontend ecosystem
- **Hugging Face** for pre-trained transformer models
- **Tailwind CSS** for utility-first styling approach
- **SEC EDGAR** for publicly available financial data

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/sujal-pawar/Financial_statement_analysis/issues)
- **Documentation**: Check this README and inline code comments
- **Community**: Join discussions in GitHub Discussions

---

**Made with ❤️ for financial analysis and transparency**

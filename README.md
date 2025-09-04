# Financial Statement Analysis Application

A comprehensive application for analyzing financial statements from PDF reports. This application combines a Python backend for PDF parsing and financial analysis with a React frontend for data visualization and exploration.

## Features

- **PDF Parsing**: Extract financial data from annual reports and financial statements
- **Financial Analysis**: Analyze income statements, balance sheets, and cash flow statements
- **Data Visualization**: Visualize financial trends and key metrics
- **QA Checks**: Automatic quality assurance checks on financial data
- **Semantic Search**: Search through financial notes and MD&A sections

## System Requirements

- **Python 3.10+**
- **Node.js 18+**
- **Windows, macOS, or Linux**

## Quick Start

For a quick start with minimal setup, use the provided `run_app.bat` script (Windows):

```bash
run_app.bat
```

This will:
1. Create a Python virtual environment (if it doesn't exist)
2. Install all Python dependencies
3. Install all Node.js dependencies
4. Start the backend server
5. Start the frontend development server

Once started, navigate to [http://localhost:3000](http://localhost:3000) in your web browser.

## Step by Step Installation

If you prefer to install and run the application manually, follow these steps:

### Backend Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/Financial_statement_analysis.git
   cd Financial_statement_analysis
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Windows:
   ```bash
   venv\Scripts\activate
   ```
   - macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. **Install Python dependencies**:
   ```bash
   pip install -r npnonlyf/requirements.txt
   ```

### Frontend Setup

1. **Navigate to the client directory**:
   ```bash
   cd client
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

## Running the Application

### Start the Backend Server

```bash
python server.py
```

The backend server will run at [http://localhost:5000](http://localhost:5000).

### Start the Frontend Server

In a new terminal, navigate to the client directory and run:

```bash
npm run dev
```

The frontend will be available at [http://localhost:3000](http://localhost:3000).

## Using the Application

### 1. Upload a Financial Statement PDF

- Click on the "Upload" button on the dashboard
- Select a financial statement PDF (annual report, 10-K filing, etc.)
- Wait for the processing to complete

### 2. Analyze Financial Data

- After processing, select a company from the dropdown
- The application will display the available years for that company
- View financial data, trends, and quality assurance findings

### 3. Search and Explore

- Use the search functionality to find specific information in the financial notes
- Export data as needed

## What Kind of PDFs Will Work?

### Supported Financial Document Types

- **Annual Reports** from publicly traded companies
- **10-K Filings** submitted to the SEC
- **Financial Statements** with clear tabular data
- Both **text-based** and **scanned** PDFs (with OCR support)

### Required Content

For best results, the PDF should contain:

1. **Income Statement** data (revenue, expenses, profits)
2. **Balance Sheet** data (assets, liabilities, equity)
3. **Cash Flow Statement** data
4. **Clear tabular data** with financial figures
5. **Financial notes** sections for semantic search

### Recommended Examples for Testing

If you're having trouble with your own PDFs, try using annual reports from major publicly traded companies, such as:

- Apple Inc.
- Microsoft Corporation
- Amazon
- Google (Alphabet Inc.)

These reports follow standard formatting and are more likely to be processed correctly.

### Testing Tips

- Name your files with patterns like "CompanyName_annual_report_2023.pdf" to help the system extract metadata
- Look for warning messages in the UI if the system can't find financial data
- The system includes a demo mode that will generate sample data if no financial data is found

## Troubleshooting

### "No financial data detected" Warning

If you receive a warning that no financial data was detected:

1. **Check your PDF**: Ensure it contains financial statements in a tabular format
2. **Try a different PDF**: Test with a standard annual report from a major company
3. **Check file format**: Make sure the PDF is not heavily secured or encrypted
4. **Look at demo data**: The system will generate sample data for demonstration purposes

### Backend Server Issues

If the backend server fails to start:

1. **Check dependencies**: Make sure all Python dependencies are installed
2. **Check port availability**: Ensure port 5000 is not in use by another application
3. **Check logs**: Review the logs in `pipeline.log` and `api.log` for specific errors

### Frontend Issues

If the frontend fails to load or connect to the backend:

1. **Check backend status**: Ensure the backend server is running
2. **Check port settings**: Verify the frontend is configured to connect to the correct backend URL
3. **Check browser console**: Look for error messages in the browser developer tools

## Developer Guide

### Backend Structure

- **server.py**: Flask API server
- **npnonlyf/pdf_parser.py**: PDF extraction logic
- **npnonlyf/pipeline.py**: Main data processing pipeline
- **npnonlyf/embeddings.py**: Text embeddings for semantic search
- **npnonlyf/qa_checks.py**: Quality assurance checks for financial data

### Frontend Structure

- **src/context/AppContext.tsx**: Main application state management
- **src/components/**: React components
- **src/services/api.ts**: API client for backend communication
- **src/types/index.ts**: TypeScript type definitions

### Adding New Features

Refer to the component architecture and API documentation in the codebase for guidance on extending the application.
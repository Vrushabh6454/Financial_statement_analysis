"""
Enhanced utility functions with robust field mapping and numeric cleaning.
"""

import os
import re
import json
import uuid
import logging
import difflib
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Comprehensive field mappings with extensive synonyms
FIELD_MAPPINGS: Dict[str, Dict[str, List[str]]] = {
    "income": {
        "revenue": [
            "revenue", "sales", "turnover", "net sales", "total revenue", "operating revenue", 
            "net interest income", "total sales", "gross sales", "sales revenue", "operating sales"
        ],
        "cost_of_goods_sold": [
            "cost of revenue", "cost of sales", "cost of goods sold", "cogs", "cost of products sold",
            "direct costs", "product costs", "manufacturing costs"
        ],
        "gross_profit": ["gross profit", "gross income", "gross margin"],
        "operating_expenses": [
            "operating expenses", "operating costs", "total operating expenses", 
            "selling general administrative", "sg&a", "sga", "administrative expenses"
        ],
        "operating_income": [
            "operating income", "operating profit", "ebit", "earnings before interest and taxes",
            "income from operations", "operating earnings"
        ],
        "interest_expense": [
            "interest expense", "interest paid", "financial costs", "interest and similar charges",
            "borrowing costs", "finance costs"
        ],
        "pretax_income": [
            "pretax income", "income before tax", "earnings before tax", "profit before tax",
            "income before income taxes", "pretax earnings"
        ],
        "income_tax": [
            "tax expense", "income tax", "provision for taxes", "tax provision", 
            "income tax expense", "current tax", "deferred tax"
        ],
        "net_income": [
            "net income", "net profit", "profit after tax", "earnings", "net earnings",
            "profit for the period", "profit attributable", "comprehensive income"
        ],
        "eps_basic": ["earnings per share", "eps", "basic eps", "basic earnings per share"],
        "eps_diluted": ["diluted eps", "diluted earnings per share"],
    },
    "balance": {
        "cash_and_equivalents": [
            "cash", "cash and equivalents", "cash and cash equivalents", 
            "cash and short term investments", "cash at bank", "bank balances"
        ],
        "accounts_receivable": [
            "accounts receivable", "receivables", "trade receivables", "customer receivables",
            "trade debtors", "amounts receivable"
        ],
        "inventory": ["inventory", "inventories", "stock", "finished goods", "raw materials"],
        "other_current_assets": ["other current assets", "prepaid expenses", "other receivables"],
        "total_current_assets": ["current assets", "total current assets"],
        "ppe": [
            "property plant equipment", "ppe", "fixed assets", "property, plant and equipment",
            "plant and equipment", "tangible assets", "buildings and equipment"
        ],
        "intangible_assets": [
            "goodwill", "intangible assets", "goodwill and intangible assets", 
            "intellectual property", "patents", "trademarks"
        ],
        "total_noncurrent_assets": ["noncurrent assets", "total noncurrent assets", "non current assets"],
        "total_assets": ["total assets", "assets"],
        "accounts_payable": [
            "accounts payable", "payables", "trade payables", "trade creditors", 
            "amounts payable", "supplier payables"
        ],
        "short_term_debt": [
            "short term debt", "current debt", "short term borrowings", "current borrowings",
            "short term loans", "current portion of debt"
        ],
        "other_current_liabilities": [
            "other current liabilities", "accrued expenses", "accrued liabilities", 
            "other payables", "provisions"
        ],
        "total_current_liabilities": ["current liabilities", "total current liabilities"],
        "long_term_debt": [
            "long term debt", "long-term debt", "non-current liabilities", "long term liabilities",
            "long term borrowings", "bonds payable", "notes payable"
        ],
        "total_noncurrent_liabilities": ["total noncurrent liabilities", "total non current liabilities"],
        "total_liabilities": ["total liabilities", "liabilities"],
        "share_capital": [
            "share capital", "common stock", "additional paid in capital", "capital stock",
            "ordinary shares", "equity shares"
        ],
        "retained_earnings": [
            "retained earnings", "accumulated earnings", "retained profit", "accumulated profit",
            "reserves", "profit reserves"
        ],
        "other_equity": [
            "accumulated other comprehensive income", "other equity", "other reserves",
            "translation reserves", "revaluation reserves"
        ],
        "total_equity": [
            "shareholders equity", "stockholders equity", "equity", "total equity",
            "owners equity", "shareholders funds", "net worth"
        ],
    },
    "cashflow": {
        "net_income": ["net income", "profit for the period", "net earnings"],
        "depreciation_amortization": [
            "depreciation", "depreciation and amortization", "amortization", 
            "depreciation expense", "amortisation"
        ],
        "working_capital_changes": [
            "working capital changes", "change in working capital", "changes in operating assets",
            "working capital adjustments"
        ],
        "cfo": [
            "cash from operating activities", "operating cash flow", "cfo", 
            "net cash from operations", "cash generated from operations"
        ],
        "capex": [
            "capital expenditures", "capex", "purchase of ppe", "capital investments",
            "additions to property plant equipment"
        ],
        "acquisitions": ["acquisitions", "business acquisitions", "purchase of subsidiaries"],
        "other_investing": ["other investing activities", "other investment activities"],
        "cfi": [
            "cash from investing activities", "investing cash flow", "cfi", 
            "net cash from investing", "cash used in investing"
        ],
        "debt_issued": ["debt issued", "proceeds from debt", "borrowings", "loans received"],
        "debt_repaid": ["debt repaid", "repayment of debt", "debt payments", "loan repayments"],
        "dividends_paid": ["dividends paid", "dividend payments", "distributions"],
        "share_buybacks": [
            "share buybacks", "repurchase of common stock", "share repurchases", 
            "treasury stock purchases"
        ],
        "other_financing": ["other financing activities", "other finance activities"],
        "cff": [
            "cash from financing activities", "financing cash flow", "cff", 
            "net cash from financing", "cash used in financing"
        ],
        "net_change_in_cash": [
            "net change in cash", "change in cash", "net cash flow", 
            "increase decrease in cash"
        ],
        "ending_cash_balance": [
            "ending cash balance", "cash at end of period", "closing cash balance",
            "cash at period end"
        ],
    },
}


def create_directory_structure():
    """Create necessary directory structure."""
    for d in ["data", "data/pdfs", "data/output", "data/embeddings"]:
        os.makedirs(d, exist_ok=True)
        logger.info(f"Ensured directory: {d}")


def get_or_create_company_id(company_name: str, id_map: Dict[str, str]) -> str:
    """Get or create UUID for company."""
    if company_name not in id_map:
        id_map[company_name] = str(uuid.uuid4())
    return id_map[company_name]


def normalize_field_name(text: str) -> str:
    """Normalize field name for mapping."""
    if not text:
        return ""
    # Remove brackets, parentheses, special characters
    text = re.sub(r'\[[^\]]*\]', ' ', str(text))
    text = re.sub(r'\([^)]*\)', ' ', text)
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fuzzy_best_match(query: str, candidates: List[str], threshold: float = 0.85) -> Optional[str]:
    """Find best fuzzy match from candidates."""
    best_match = None
    best_score = 0.0
    
    for candidate in candidates:
        score = difflib.SequenceMatcher(None, query, candidate).ratio()
        if score > best_score and score >= threshold:
            best_score = score
            best_match = candidate
            
    return best_match


def map_to_canonical_field(text: str, statement_type: str) -> Optional[str]:
    """Map raw field name to canonical field using comprehensive synonyms and fuzzy matching."""
    if statement_type not in FIELD_MAPPINGS:
        return None
        
    normalized = normalize_field_name(text)
    if not normalized:
        return None
    
    # First try exact synonym matching
    for canonical_field, synonyms in FIELD_MAPPINGS[statement_type].items():
        for synonym in synonyms:
            if re.search(rf'\b{re.escape(synonym)}\b', normalized):
                return canonical_field
    
    # Fallback to fuzzy matching
    all_synonyms = {}
    for canonical_field, synonyms in FIELD_MAPPINGS[statement_type].items():
        for synonym in synonyms:
            all_synonyms[synonym] = canonical_field
    
    fuzzy_match = fuzzy_best_match(normalized, list(all_synonyms.keys()))
    if fuzzy_match:
        return all_synonyms[fuzzy_match]
        
    return None


def clean_numeric_value(value: Any) -> Optional[float]:
    """Robust numeric cleaning for financial values."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
        
    text = str(value).strip()
    if not text or text.lower() in {'n/a', 'na', '—', '–', '-', 'nil', 'none'}:
        return None
    
    # Handle unicode minus signs
    text = text.replace('\u2212', '-').replace('−', '-')
    
    # Remove currency symbols
    for symbol in ['$', '€', '£', '¥', '₹', '¢']:
        text = text.replace(symbol, '')
    
    # Remove commas and whitespace
    text = re.sub(r'[,\s]+', '', text)
    
    # Handle negative numbers in parentheses
    if text.startswith('(') and text.endswith(')'):
        text = '-' + text[1:-1]
    
    # Extract numeric pattern
    pattern = r'-?\d{1,3}(?:,?\d{3})*(?:\.\d+)?'
    match = re.search(pattern, text.replace(',', ''))
    
    if not match:
        return None
        
    try:
        return float(match.group().replace(',', ''))
    except (ValueError, AttributeError):
        return None


def process_financial_data(
    financial_data: List[Dict[str, Any]], 
    company_id_map: Dict[str, str]
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Process raw financial data into structured DataFrames."""
    if not financial_data:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Aggregate data by company/year/field
    temp_data: Dict[str, Dict[int, Dict[str, Any]]] = defaultdict(lambda: defaultdict(dict))
    
    for item in financial_data:
        company = item.get("company", "Unknown")
        year = int(item.get("year", 0) or 0)
        raw_field = item.get("field", "")
        value = item.get("value", None)
        statement_type = item.get("statement_type", "unknown")
        currency = item.get("currency", "USD")

        company_id = get_or_create_company_id(company, company_id_map)
        
        # Map to canonical field
        canonical_field = map_to_canonical_field(raw_field, statement_type)
        if not canonical_field:
            # Log unmapped fields for debugging
            logger.debug(f"Unmapped field: {raw_field} (type: {statement_type})")
            continue

        # Store in temporary structure
        temp_data[company_id][year][canonical_field] = value
        temp_data[company_id][year]["currency"] = currency

    # Convert to DataFrames
    income_rows: List[Dict[str, Any]] = []
    balance_rows: List[Dict[str, Any]] = []
    cashflow_rows: List[Dict[str, Any]] = []

    for company_id, years in temp_data.items():
        for year, fields in years.items():
            base_row = {"company_id": company_id, "year": year, "currency": fields.get("currency", "USD")}
            
            # Separate by statement type
            income_fields = {k: v for k, v in fields.items() if k in FIELD_MAPPINGS["income"]}
            balance_fields = {k: v for k, v in fields.items() if k in FIELD_MAPPINGS["balance"]}
            cashflow_fields = {k: v for k, v in fields.items() if k in FIELD_MAPPINGS["cashflow"]}

            if income_fields:
                income_rows.append({**base_row, **income_fields})
            if balance_fields:
                balance_rows.append({**base_row, **balance_fields})
            if cashflow_fields:
                cashflow_rows.append({**base_row, **cashflow_fields})

    # Create DataFrames with consistent column order
    income_columns = ["company_id", "year", "currency"] + list(FIELD_MAPPINGS["income"].keys())
    balance_columns = ["company_id", "year", "currency"] + list(FIELD_MAPPINGS["balance"].keys())
    cashflow_columns = ["company_id", "year", "currency"] + list(FIELD_MAPPINGS["cashflow"].keys())

    income_df = pd.DataFrame(income_rows).reindex(columns=income_columns)
    balance_df = pd.DataFrame(balance_rows).reindex(columns=balance_columns)
    cashflow_df = pd.DataFrame(cashflow_rows).reindex(columns=cashflow_columns)

    # Log coverage statistics
    logger.info(f"Data coverage: Income={len(income_df)} rows, Balance={len(balance_df)} rows, Cashflow={len(cashflow_df)} rows")
    
    return income_df, balance_df, cashflow_df


def calculate_features(
    income_df: pd.DataFrame, 
    balance_df: pd.DataFrame, 
    cashflow_df: pd.DataFrame
) -> pd.DataFrame:
    """Calculate financial ratios and features."""
    if income_df.empty or balance_df.empty or cashflow_df.empty:
        return pd.DataFrame()

    features_list: List[Dict[str, Any]] = []
    
    # Get all companies
    companies = set()
    for df in [income_df, balance_df, cashflow_df]:
        if "company_id" in df.columns:
            companies.update(df["company_id"].dropna().unique())

    for company_id in companies:
        # Filter data for this company
        inc_data = income_df[income_df["company_id"] == company_id] if "company_id" in income_df.columns else pd.DataFrame()
        bal_data = balance_df[balance_df["company_id"] == company_id] if "company_id" in balance_df.columns else pd.DataFrame()
        cf_data = cashflow_df[cashflow_df["company_id"] == company_id] if "company_id" in cashflow_df.columns else pd.DataFrame()
        
        # Get all years for this company
        years = set()
        for df in [inc_data, bal_data, cf_data]:
            if "year" in df.columns:
                years.update(df["year"].dropna().astype(int))
        
        for year in sorted(years):
            def get_value(df: pd.DataFrame, field: str) -> Optional[float]:
                """Helper to get field value for specific year."""
                if df.empty or field not in df.columns or "year" not in df.columns:
                    return None
                year_data = df[df["year"] == year]
                if year_data.empty:
                    return None
                value = year_data.iloc[0].get(field)
                return value if pd.notna(value) else None

            # Get key financial metrics
            revenue = get_value(inc_data, "revenue")
            cogs = get_value(inc_data, "cost_of_goods_sold")
            gross_profit = get_value(inc_data, "gross_profit")
            net_income = get_value(inc_data, "net_income")
            operating_income = get_value(inc_data, "operating_income")
            interest_expense = get_value(inc_data, "interest_expense")
            
            total_assets = get_value(bal_data, "total_assets")
            total_equity = get_value(bal_data, "total_equity")
            total_liabilities = get_value(bal_data, "total_liabilities")
            current_assets = get_value(bal_data, "total_current_assets")
            current_liabilities = get_value(bal_data, "total_current_liabilities")
            cash = get_value(bal_data, "cash_and_equivalents")
            receivables = get_value(bal_data, "accounts_receivable")
            inventory = get_value(bal_data, "inventory")
            
            cfo = get_value(cf_data, "cfo")
            
            # Calculate ratios
            row = {"company_id": company_id, "year": int(year)}
            
            # Liquidity ratios
            row["current_ratio"] = (current_assets / current_liabilities) if (current_assets and current_liabilities) else None
            row["quick_ratio"] = ((cash or 0) + (receivables or 0)) / current_liabilities if current_liabilities else None
            
            # Leverage ratios
            row["debt_to_equity"] = (total_liabilities / total_equity) if (total_liabilities and total_equity) else None
            row["interest_coverage"] = (operating_income / interest_expense) if (operating_income and interest_expense) else None
            
            # Profitability ratios
            row["gross_margin"] = (gross_profit / revenue) if (gross_profit and revenue) else None
            row["net_margin"] = (net_income / revenue) if (net_income and revenue) else None
            row["roa"] = (net_income / total_assets) if (net_income and total_assets) else None
            row["roe"] = (net_income / total_equity) if (net_income and total_equity) else None
            
            # Efficiency ratios
            row["cfo_to_net_income"] = (cfo / net_income) if (cfo and net_income) else None
            row["inventory_turnover"] = (cogs / inventory) if (cogs and inventory) else None
            row["receivables_days"] = (receivables / (revenue / 365)) if (receivables and revenue) else None
            
            features_list.append(row)

    return pd.DataFrame(features_list)


def save_json(data: Any, filepath: str) -> None:
    """Save data to JSON file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"Saved JSON to {filepath}")
    except Exception as e:
        logger.error(f"Error saving JSON to {filepath}: {e}")


def load_json(filepath: str) -> Optional[Any]:
    """Load data from JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Loaded JSON from {filepath}")
        return data
    except Exception as e:
        logger.error(f"Error loading JSON from {filepath}: {e}")
        return None

# utils.py

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

# --- Field Mappings and Synonyms ---
# Comprehensive field mappings with extensive synonyms. This is used to normalize
# field names found during both table and regex extraction.
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
            "pretax income", "pretax earnings", "income before tax", "earnings before tax",
            "profit before tax", "pbt"
        ],
        "income_tax": [
            "tax expense", "income tax", "provision for taxes", "tax provision", "current tax",
            "deferred tax"
        ],
        "net_income": [
            "net income", "net profit", "net earnings", "profit after tax", "pat",
            "profit for the period", "comprehensive income"
        ],
        "eps_basic": ["basic earnings per share", "basic eps", "eps basic"],
        "eps_diluted": ["diluted eps", "diluted earnings per share", "eps diluted"]
    },
    "balance": {
        "cash_and_equivalents": ["cash and equivalents", "cash", "bank balances", "cash at bank"],
        "accounts_receivable": ["accounts receivable", "trade receivables", "debtors", "customer receivables"],
        "inventory": ["inventory", "inventories", "stock", "finished goods", "raw materials"],
        "other_current_assets": ["other current assets", "prepaid expenses", "other receivables"],
        "total_current_assets": ["total current assets", "current assets"],
        "ppe": ["property plant equipment", "ppe", "fixed assets", "tangible assets", "property"],
        "intangible_assets": ["intangible assets", "goodwill", "intellectual property"],
        "total_noncurrent_assets": ["total non-current assets", "total noncurrent assets", "noncurrent assets"],
        "total_assets": ["total assets", "assets"],
        "accounts_payable": ["accounts payable", "trade payables", "creditors", "supplier payables"],
        "short_term_debt": ["short-term debt", "short term debt", "current debt", "current borrowings", "current portion of debt"],
        "other_current_liabilities": ["other current liabilities", "accrued expenses", "accrued liabilities"],
        "total_current_liabilities": ["total current liabilities", "current liabilities"],
        "long_term_debt": ["long-term debt", "long term debt", "non-current liabilities", "bonds payable"],
        "total_noncurrent_liabilities": ["total non-current liabilities", "total noncurrent liabilities", "non-current liabilities"],
        "total_liabilities": ["total liabilities", "liabilities"],
        "share_capital": ["share capital", "common stock", "equity shares", "capital stock"],
        "retained_earnings": ["retained earnings", "retained profit", "accumulated earnings", "reserves"],
        "other_equity": ["other equity", "other comprehensive income", "translation reserves"],
        "total_equity": ["total equity", "shareholders equity", "stockholders equity", "net worth"]
    },
    "cashflow": {
        "net_income": ["net income", "net profit", "profit for the period"],
        "depreciation_amortization": ["depreciation and amortization", "depreciation", "amortization"],
        "working_capital_changes": ["changes in working capital", "working capital"],
        "cfo": ["net cash from operating activities", "operating cash flow", "cfo"],
        "capex": ["capital expenditures", "capex", "purchase of ppe", "additions to property"],
        "acquisitions": ["acquisitions", "purchase of subsidiaries"],
        "other_investing": ["other investing activities"],
        "cfi": ["net cash from investing activities", "investing cash flow", "cfi"],
        "debt_issued": ["proceeds from debt", "debt issued", "borrowings received"],
        "debt_repaid": ["repayment of debt", "debt repayments", "loan repayments"],
        "dividends_paid": ["dividends paid", "distributions"],
        "share_buybacks": ["share buybacks", "share repurchases"],
        "other_financing": ["other financing activities"],
        "cff": ["net cash from financing activities", "financing cash flow", "cff"],
        "net_change_in_cash": ["net change in cash", "change in cash", "net cash flow"],
        "ending_cash_balance": ["ending cash balance", "cash at end of period"]
    }
}

# --- Data Cleaning and Formatting Functions ---

def clean_numeric_value(value: Any) -> Optional[float]:
    """
    Cleans and converts text values to numeric values, handling various formats.
    """
    if pd.isna(value) or value is None:
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if not isinstance(value, str):
        value = str(value)
    
    # Replace non-breaking spaces and other special characters
    value = value.replace('\xa0', '').replace('—', '0').strip()
    
    # Handle negative numbers in parentheses
    if value.startswith('(') and value.endswith(')'):
        value = '-' + value.strip('()')
    
    # Remove commas, currency symbols, and percentage signs
    value = re.sub(r'[$,%]', '', value).strip()
    
    # Find a sequence of digits and an optional decimal point
    numeric_match = re.search(r'-?\d{1,3}(?:,\d{3})*(?:\.\d+)?', value)
    if numeric_match:
        try:
            # Remove all commas before converting to float
            return float(numeric_match.group().replace(',', ''))
        except ValueError:
            return None
    return None

def map_to_canonical_field(field_name: str, statement_type: str) -> Optional[str]:
    """Maps a given field name to its canonical name using fuzzy matching and a predefined list."""
    field_name_lower = field_name.lower()
    
    for canonical_name, synonyms in FIELD_MAPPINGS.get(statement_type, {}).items():
        if field_name_lower in [s.lower() for s in synonyms]:
            return canonical_name
        # Use fuzzy matching for close names
        matches = difflib.get_close_matches(field_name_lower, [s.lower() for s in synonyms], n=1, cutoff=0.8)
        if matches:
            return canonical_name
    return None

# --- Pipeline-specific Functions ---

def create_directory_structure():
    """Create necessary directories if they don't exist."""
    directories = ["data", "data/pdfs", "data/output", "data/embeddings"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory: {directory}")

def process_financial_data(financial_data: List[Dict], company_id_map: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Process raw extracted financial data into structured DataFrames.
    """
    if not financial_data:
        logger.warning("No financial data to process.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df = pd.DataFrame(financial_data)
    
    # Normalize company names to UUIDs for consistency
    company_ids = {}
    for company_name in df['company'].unique():
        company_id = company_id_map.get(company_name)
        if not company_id:
            company_id = str(uuid.uuid4())
            company_id_map[company_name] = company_id
        company_ids[company_name] = company_id
    
    df['company_id'] = df['company'].map(company_ids)
    
    # Pivot the tables for easier analysis
    income_df = df[df['statement_type'] == 'income'].pivot_table(
        index=['company_id', 'year'], 
        columns='field', 
        values='value', 
        aggfunc='first'
    ).reset_index()

    balance_df = df[df['statement_type'] == 'balance'].pivot_table(
        index=['company_id', 'year'], 
        columns='field', 
        values='value', 
        aggfunc='first'
    ).reset_index()

    cashflow_df = df[df['statement_type'] == 'cashflow'].pivot_table(
        index=['company_id', 'year'], 
        columns='field', 
        values='value', 
        aggfunc='first'
    ).reset_index()

    logger.info(f"Data coverage: Income={len(income_df)} rows, Balance={len(balance_df)} rows, Cashflow={len(cashflow_df)} rows")
    
    return income_df, balance_df, cashflow_df


def calculate_features(income_df: pd.DataFrame, balance_df: pd.DataFrame, cashflow_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates key financial ratios and features.
    """
    merged_df = pd.merge(income_df, balance_df, on=['company_id', 'year'], suffixes=('_inc', '_bal'), how='outer')
    merged_df = pd.merge(merged_df, cashflow_df, on=['company_id', 'year'], suffixes=('', '_cf'), how='outer')

    features_list = []
    
    for _, row in merged_df.iterrows():
        company_id, year = row['company_id'], row['year']
        
        # Pull key values with a fallback to None
        revenue = row.get("revenue")
        net_income = row.get("net_income")
        total_assets = row.get("total_assets")
        total_equity = row.get("total_equity")
        total_liabilities = row.get("total_liabilities")
        cfo = row.get("cfo")
        cogs = row.get("cost_of_goods_sold")
        inventory = row.get("inventory")
        receivables = row.get("accounts_receivable")
        current_assets = row.get("total_current_assets")
        current_liabilities = row.get("total_current_liabilities")
        short_term_debt = row.get("short_term_debt")
        long_term_debt = row.get("long_term_debt")
        pretax_income = row.get("pretax_income")
        interest_expense = row.get("interest_expense")
        
        # Ensure that values used in calculations are not NaN
        revenue = revenue if pd.notna(revenue) else None
        net_income = net_income if pd.notna(net_income) else None
        total_assets = total_assets if pd.notna(total_assets) else None
        total_equity = total_equity if pd.notna(total_equity) else None
        total_liabilities = total_liabilities if pd.notna(total_liabilities) else None
        cfo = cfo if pd.notna(cfo) else None
        cogs = cogs if pd.notna(cogs) else None
        inventory = inventory if pd.notna(inventory) else None
        receivables = receivables if pd.notna(receivables) else None
        current_assets = current_assets if pd.notna(current_assets) else None
        current_liabilities = current_liabilities if pd.notna(current_liabilities) else None
        short_term_debt = short_term_debt if pd.notna(short_term_debt) else None
        long_term_debt = long_term_debt if pd.notna(long_term_debt) else None
        pretax_income = pretax_income if pd.notna(pretax_income) else None
        interest_expense = interest_expense if pd.notna(interest_expense) else None

        # Add all available fields to the output row
        output_row = {
            'company_id': company_id,
            'year': year,
            'revenue': revenue,
            'net_income': net_income,
            'total_assets': total_assets,
            'total_equity': total_equity,
            'total_liabilities': total_liabilities,
            'cfo': cfo,
            'cogs': cogs,
            'inventory': inventory,
            'receivables': receivables,
            'current_assets': current_assets,
            'current_liabilities': current_liabilities,
            'short_term_debt': short_term_debt,
            'long_term_debt': long_term_debt,
            'pretax_income': pretax_income,
            'interest_expense': interest_expense,
        }
        
        # Profitability Ratios
        output_row["gross_margin"] = (row.get("gross_profit") / revenue) if (row.get("gross_profit") and revenue) else None
        output_row["operating_margin"] = (row.get("operating_income") / revenue) if (row.get("operating_income") and revenue) else None
        output_row["net_margin"] = (net_income / revenue) if (net_income and revenue) else None
        output_row["roa"] = (net_income / total_assets) if (net_income and total_assets) else None
        output_row["roe"] = (net_income / total_equity) if (net_income and total_equity) else None
        
        # Liquidity Ratios
        output_row["current_ratio"] = (current_assets / current_liabilities) if (current_assets and current_liabilities) else None

        # Leverage Ratios
        total_debt = short_term_debt + long_term_debt if short_term_debt is not None and long_term_debt is not None else None
        output_row["debt_to_equity"] = (total_debt / total_equity) if (total_debt and total_equity) else None
        output_row["interest_coverage"] = (pretax_income + interest_expense) / interest_expense if (pretax_income is not None and interest_expense is not None and interest_expense != 0) else None

        # Efficiency Ratios
        output_row["cfo_to_net_income"] = (cfo / net_income) if (cfo and net_income) else None
        output_row["inventory_turnover"] = (cogs / inventory) if (cogs and inventory) else None
        output_row["receivables_days"] = (receivables / (revenue / 365)) if (receivables and revenue) else None
        
        features_list.append(output_row)

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
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while loading {filepath}: {e}")
        return None
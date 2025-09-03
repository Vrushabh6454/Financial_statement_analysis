"""
Utility functions for financial statement analysis pipeline.
"""

import re
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
import uuid
from collections import defaultdict
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Financial statement field mappings
FIELD_MAPPINGS = {
    'income': {
        'revenue': ['revenue', 'sales', 'turnover', 'net sales', 'total revenue', 'operating revenue', 'net interest income'],
        'cost_of_goods_sold': ['cost of revenue', 'cost of sales', 'cost of goods sold', 'cogs'],
        'gross_profit': ['gross profit', 'gross income'],
        'operating_expenses': ['operating expenses', 'operating costs', 'total operating expenses', 'selling general administrative'],
        'operating_income': ['operating income', 'operating profit', 'ebit', 'earnings before interest and taxes'],
        'interest_expense': ['interest expense', 'interest paid', 'financial costs', 'interest and similar charges'],
        'pretax_income': ['pretax income', 'income before tax', 'earnings before tax', 'profit before tax'],
        'income_tax': ['tax expense', 'income tax', 'provision for taxes', 'tax provision'],
        'net_income': ['net income', 'net profit', 'profit after tax', 'earnings', 'net earnings'],
        'eps_basic': ['earnings per share', 'eps', 'basic eps'],
        'eps_diluted': ['diluted eps']
    },
    'balance': {
        'cash_and_equivalents': ['cash', 'cash and equivalents', 'cash and cash equivalents', 'cash and short term investments'],
        'accounts_receivable': ['accounts receivable', 'receivables', 'trade receivables', 'customer receivables'],
        'inventory': ['inventory', 'inventories', 'stock'],
        'other_current_assets': ['other current assets'],
        'total_current_assets': ['current assets', 'total current assets'],
        'ppe': ['property plant equipment', 'ppe', 'fixed assets', 'property, plant and equipment'],
        'intangible_assets': ['goodwill', 'intangible assets', 'goodwill and intangible assets'],
        'total_noncurrent_assets': ['noncurrent assets', 'total noncurrent assets'],
        'total_assets': ['total assets', 'assets'],
        'accounts_payable': ['accounts payable', 'payables', 'trade payables'],
        'short_term_debt': ['short term debt', 'current debt'],
        'other_current_liabilities': ['other current liabilities'],
        'total_current_liabilities': ['current liabilities', 'total current liabilities'],
        'long_term_debt': ['long term debt', 'long-term debt', 'non-current liabilities', 'long term liabilities'],
        'total_noncurrent_liabilities': ['total noncurrent liabilities'],
        'total_liabilities': ['total liabilities', 'liabilities'],
        'share_capital': ['share capital', 'common stock', 'additional paid in capital'],
        'retained_earnings': ['retained earnings', 'accumulated earnings', 'retained profit'],
        'other_equity': ['accumulated other comprehensive income', 'other equity'],
        'total_equity': ['shareholders equity', 'stockholders equity', 'equity', 'total equity']
    },
    'cashflow': {
        'net_income': ['net income'],
        'depreciation_amortization': ['depreciation', 'depreciation and amortization', 'amortization'],
        'working_capital_changes': ['working capital changes', 'change in working capital'],
        'cfo': ['cash from operating activities', 'operating cash flow', 'cfo', 'net cash from operations'],
        'capex': ['capital expenditures', 'capex', 'purchase of ppe'],
        'acquisitions': ['acquisitions'],
        'other_investing': ['other investing activities'],
        'cfi': ['cash from investing activities', 'investing cash flow', 'cfi', 'net cash from investing'],
        'debt_issued': ['debt issued', 'proceeds from debt'],
        'debt_repaid': ['debt repaid', 'repayment of debt'],
        'dividends_paid': ['dividends paid'],
        'share_buybacks': ['share buybacks', 'repurchase of common stock'],
        'other_financing': ['other financing activities'],
        'cff': ['cash from financing activities', 'financing cash flow', 'cff', 'net cash from financing'],
        'net_change_in_cash': ['net change in cash', 'change in cash', 'net cash flow'],
        'ending_cash_balance': ['ending cash balance', 'cash at end of period']
    }
}


def create_directory_structure():
    """Create necessary directory structure for the pipeline."""
    directories = [
        'data',
        'data/pdfs',
        'data/output',
        'data/embeddings'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def get_or_create_company_id(company_name: str, id_map: Dict) -> str:
    """Gets or creates a UUID for a company."""
    if company_name not in id_map:
        id_map[company_name] = str(uuid.uuid4())
    return id_map[company_name]


def process_financial_data(financial_data: List[Dict], company_id_map: Dict) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Standardize raw financial data and structure it into three core DataFrames.
    """
    income_cols = ['company_id', 'year', 'currency'] + list(FIELD_MAPPINGS['income'].keys())
    balance_cols = ['company_id', 'year', 'currency'] + list(FIELD_MAPPINGS['balance'].keys())
    cashflow_cols = ['company_id', 'year', 'currency'] + list(FIELD_MAPPINGS['cashflow'].keys())
    
    if not financial_data:
        logger.warning("No financial data to process. Returning empty DataFrames.")
        return pd.DataFrame(columns=income_cols), pd.DataFrame(columns=balance_cols), pd.DataFrame(columns=cashflow_cols)

    temp_data = defaultdict(lambda: defaultdict(dict))

    for item in financial_data:
        company = item.get('company')
        year = item.get('year')
        raw_field = item.get('field')
        value = item.get('value')
        statement_type = item.get('statement_type')

        company_id = get_or_create_company_id(company, company_id_map)
        
        canonical_field = map_to_canonical_field(raw_field, statement_type)
        if not canonical_field:
            continue
        
        # Aggregate data by company, year, and statement type
        temp_data[company_id][year][canonical_field] = value
    
    income_data, balance_data, cashflow_data = [], [], []

    for company_id, years in temp_data.items():
        for year, fields in years.items():
            fields['company_id'] = company_id
            fields['year'] = year
            fields['currency'] = 'USD'
            
            # Separate data into the three statements
            inc_row = {k: v for k, v in fields.items() if k in FIELD_MAPPINGS['income']}
            bal_row = {k: v for k, v in fields.items() if k in FIELD_MAPPINGS['balance']}
            cf_row = {k: v for k, v in fields.items() if k in FIELD_MAPPINGS['cashflow']}
            
            if inc_row:
                inc_row.update({'company_id': company_id, 'year': year, 'currency': 'USD'})
                income_data.append(inc_row)
            if bal_row:
                bal_row.update({'company_id': company_id, 'year': year, 'currency': 'USD'})
                balance_data.append(bal_row)
            if cf_row:
                cf_row.update({'company_id': company_id, 'year': year, 'currency': 'USD'})
                cashflow_data.append(cf_row)
    
    income_cols = ['company_id', 'year', 'currency'] + list(FIELD_MAPPINGS['income'].keys())
    balance_cols = ['company_id', 'year', 'currency'] + list(FIELD_MAPPINGS['balance'].keys())
    cashflow_cols = ['company_id', 'year', 'currency'] + list(FIELD_MAPPINGS['cashflow'].keys())

    income_df = pd.DataFrame(income_data).reindex(columns=income_cols)
    balance_df = pd.DataFrame(balance_data).reindex(columns=balance_cols)
    cashflow_df = pd.DataFrame(cashflow_data).reindex(columns=cashflow_cols)
    
    return income_df, balance_df, cashflow_df


def calculate_features(income_df: pd.DataFrame, balance_df: pd.DataFrame, cashflow_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates key financial ratios and features.
    """
    if income_df.empty or balance_df.empty or cashflow_df.empty:
        return pd.DataFrame()

    features_list = []
    companies = income_df['company_id'].unique()

    for company_id in companies:
        inc_comp = income_df[income_df['company_id'] == company_id]
        bal_comp = balance_df[balance_df['company_id'] == company_id]
        cf_comp = cashflow_df[cashflow_df['company_id'] == company_id]

        years = sorted(list(set(inc_comp['year']) | set(bal_comp['year']) | set(cf_comp['year'])))
        
        for year in years:
            inc_year = inc_comp[inc_comp['year'] == year]
            bal_year = bal_comp[bal_comp['year'] == year]
            cf_year = cf_comp[cf_comp['year'] == year]

            if inc_year.empty or bal_year.empty or cf_year.empty:
                continue

            row = {'company_id': company_id, 'year': year}
            
            def get_val(df, col):
                if not df.empty and col in df.columns:
                    val = df.iloc[0][col]
                    return val if pd.notna(val) else None
                return None

            revenue = get_val(inc_year, 'revenue')
            cogs = get_val(inc_year, 'cost_of_goods_sold')
            gross_profit = get_val(inc_year, 'gross_profit')
            net_income = get_val(inc_year, 'net_income')
            ebit = get_val(inc_year, 'operating_income')
            interest_expense = get_val(inc_year, 'interest_expense')
            total_assets = get_val(bal_year, 'total_assets')
            total_equity = get_val(bal_year, 'total_equity')
            current_assets = get_val(bal_year, 'total_current_assets')
            current_liabilities = get_val(bal_year, 'total_current_liabilities')
            cash = get_val(bal_year, 'cash_and_equivalents')
            receivables = get_val(bal_year, 'accounts_receivable')
            inventory = get_val(bal_year, 'inventory')
            cfo = get_val(cf_year, 'cfo')
            
            row['current_ratio'] = (current_assets / current_liabilities) if (current_assets and current_liabilities and current_liabilities != 0) else None
            row['quick_ratio'] = ((cash + receivables) / current_liabilities) if (cash and receivables and current_liabilities and current_liabilities != 0) else None
            row['debt_to_equity'] = (get_val(bal_year, 'total_liabilities') / total_equity) if (total_equity and total_equity != 0 and get_val(bal_year, 'total_liabilities')) else None
            row['interest_coverage'] = (ebit / interest_expense) if (ebit and interest_expense and interest_expense != 0) else None
            row['gross_margin'] = (gross_profit / revenue) if (gross_profit and revenue and revenue != 0) else None
            row['net_margin'] = (net_income / revenue) if (net_income and revenue and revenue != 0) else None
            row['roa'] = (net_income / total_assets) if (net_income and total_assets and total_assets != 0) else None
            row['roe'] = (net_income / total_equity) if (net_income and total_equity and total_equity != 0) else None
            row['cfo_to_net_income'] = (cfo / net_income) if (cfo and net_income and net_income != 0) else None
            row['inventory_turnover'] = (cogs / inventory) if (cogs and inventory and inventory != 0) else None
            row['receivables_days'] = (receivables / (revenue / 365)) if (receivables and revenue and revenue != 0) else None
            
            features_list.append(row)
    
    return pd.DataFrame(features_list)


def save_json(data: Any, filepath: str) -> None:
    """
    Save data to JSON file with error handling.
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Saved JSON data to {filepath}")
    except Exception as e:
        logger.error(f"Error saving JSON to {filepath}: {e}")
        
def load_json(filepath: str) -> Optional[Any]:
    """
    Load data from JSON file with error handling.
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded JSON data from {filepath}")
        return data
    except Exception as e:
        logger.error(f"Error loading JSON from {filepath}: {e}")
        return None


def map_to_canonical_field(text: str, statement_type: str) -> Optional[str]:
    """
    Map raw field names to canonical field names using synonym mappings.
    """
    if statement_type not in FIELD_MAPPINGS:
        return None
    
    def normalize_field_name(text: str) -> str:
        if not text:
            return ""
        normalized = re.sub(r'[^\w\s]', ' ', text.lower().strip())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    normalized_text = normalize_field_name(text)
    
    for canonical_field, synonyms in FIELD_MAPPINGS[statement_type].items():
        for synonym in synonyms:
            if synonym in normalized_text or normalized_text in synonym:
                return canonical_field
    
    return None


def clean_numeric_value(value: Any) -> Optional[float]:
    """
    Clean and convert text values to numeric values.
    """
    if pd.isna(value) or value is None:
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if not isinstance(value, str):
        value = str(value)
    
    value = value.replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
    value = value.replace('%', '').strip()
    
    if value.startswith('-') and value.endswith(''):
        value = '-' + value[1:-1] if len(value) > 2 else value
    
    numeric_match = re.search(r'-?\d+(?:\.\d+)?', value)
    if numeric_match:
        try:
            return float(numeric_match.group())
        except ValueError:
            return None
    
    return None
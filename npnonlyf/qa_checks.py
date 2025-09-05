"""
Quality assurance checks for financial statement data.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Map check_type to the new schema
QA_RULE_MAPPING = {
    'balance_equation': ('BS001', 'Assets = Liabilities + Equity'),
    'net_income_consistency': ('IS001', 'Net Income vs Retained Earnings'),
    'cash_flow_reconciliation': ('CF001', 'Cash Flow Reconciliation'),
    'quality_of_earnings': ('CF002', 'Operating Cash Flow vs Net Income'),
    'significant_revenue_decline': ('IS002', 'Significant YoY Revenue Drop'),
    'debt_vs_revenue': ('BS002', 'Increasing Debt vs Revenue Growth'),
    'profit_vs_cash_flow': ('CF003', 'Negative Cash Flow Despite Profit'),
    'low_liquidity': ('BS003', 'Low Liquidity Ratio'),
    'low_interest_coverage': ('IS003', 'Low Interest Coverage Ratio'),
    'negative_equity': ('BS004', 'Negative Shareholders Equity'),
    'negative_operating_cf': ('CF004', 'Negative Operating Cash Flow'),
    'missing_data': ('MISC001', 'Missing Key Financial Data')
}


class FinancialQAChecker:
    """
    Automated quality assurance checks for financial statements.
    """
    
    def __init__(self, tolerance: float = 0.01):
        """
        Initialize QA checker.
        """
        self.tolerance = tolerance
        self.findings = []
    
    def run_all_checks(self, income_df: pd.DataFrame, balance_df: pd.DataFrame, 
                      cashflow_df: pd.DataFrame) -> List[Dict]:
        """
        Run all QA checks on financial statement data.
        """
        self.findings = []
        
        logger.info("Starting comprehensive QA checks...")
        
        companies = set(income_df['company_id'].unique()) | set(balance_df['company_id'].unique()) | set(cashflow_df['company_id'].unique())
        
        for company_id in companies:
            company_income = income_df[income_df['company_id'] == company_id]
            company_balance = balance_df[balance_df['company_id'] == company_id]
            company_cashflow = cashflow_df[cashflow_df['company_id'] == company_id]
            
            years = sorted(list(set(company_income['year'].unique()) | set(company_balance['year'].unique()) | set(company_cashflow['year'].unique())))
            
            for year in years:
                self._check_balance_sheet_equation(company_id, year, company_balance)
                self._check_net_income_consistency(company_id, year, company_income, company_balance)
                self._check_cash_flow_reconciliation(company_id, year, company_balance, company_cashflow)
                self._check_financial_anomalies(company_id, year, company_income, company_balance, company_cashflow)
                self._check_quality_of_earnings(company_id, year, company_income, company_cashflow)
                self._check_revenue_margin_drops(company_id, year, company_income)
                self._check_debt_growth(company_id, year, company_balance, company_income)
                self._check_cash_flow_vs_profit(company_id, year, company_income, company_cashflow)
                self._check_data_completeness(company_id, year, company_income, company_balance, company_cashflow)

        logger.info(f"QA checks completed. Found {len(self.findings)} findings.")
        return self.findings
    
    def _get_field_value(self, df: pd.DataFrame, company_id: str, year: int, field: str) -> Optional[float]:
        """Helper method to get field value for specific company-year."""
        if df.empty or field not in df.columns:
            return None
        
        filtered = df[(df['company_id'] == company_id) & (df['year'] == year)]
        if not filtered.empty:
            val = filtered[field].iloc[0]
            return val if pd.notna(val) else None
        return None

    def _check_balance_sheet_equation(self, company_id: str, year: int, balance_df: pd.DataFrame):
        total_assets = self._get_field_value(balance_df, company_id, year, 'total_assets')
        total_liabilities = self._get_field_value(balance_df, company_id, year, 'total_liabilities')
        shareholders_equity = self._get_field_value(balance_df, company_id, year, 'total_equity')
        
        if total_assets is not None and total_liabilities is not None and shareholders_equity is not None:
            if total_assets != 0 and abs(total_assets - (total_liabilities + shareholders_equity)) > abs(total_assets * self.tolerance):
                self._add_finding(company_id, year, 'balance_equation', 'High', 'Assets != Liabilities + Equity.')

    def _check_net_income_consistency(self, company_id: str, year: int, income_df: pd.DataFrame, balance_df: pd.DataFrame):
        net_income = self._get_field_value(income_df, company_id, year, 'net_income')
        current_re = self._get_field_value(balance_df, company_id, year, 'retained_earnings')
        previous_re = self._get_field_value(balance_df, company_id, year - 1, 'retained_earnings')
        
        if net_income is not None and current_re is not None and previous_re is not None:
            expected_re = previous_re + net_income
            if net_income != 0 and abs(current_re - expected_re) > abs(net_income * 0.1):
                self._add_finding(company_id, year, 'net_income_consistency', 'Medium', 'Net income may not tie to retained earnings change (could be due to dividends).')

    def _check_cash_flow_reconciliation(self, company_id: str, year: int, balance_df: pd.DataFrame, cashflow_df: pd.DataFrame):
        net_change_in_cash = self._get_field_value(cashflow_df, company_id, year, 'net_change_in_cash')
        current_cash = self._get_field_value(balance_df, company_id, year, 'cash_and_equivalents')
        previous_cash = self._get_field_value(balance_df, company_id, year - 1, 'cash_and_equivalents')
        
        if net_change_in_cash is not None and current_cash is not None and previous_cash is not None:
            bs_change = current_cash - previous_cash
            if current_cash != 0 and abs(bs_change - net_change_in_cash) > abs(current_cash * self.tolerance):
                self._add_finding(company_id, year, 'cash_flow_reconciliation', 'Medium', 'Cash flow statement may not reconcile with balance sheet.')

    def _check_quality_of_earnings(self, company_id: str, year: int, income_df: pd.DataFrame, cashflow_df: pd.DataFrame):
        net_income = self._get_field_value(income_df, company_id, year, 'net_income')
        cfo = self._get_field_value(cashflow_df, company_id, year, 'cfo')
        
        if net_income is not None and cfo is not None and net_income > 0 and cfo < net_income * 0.8:
            self._add_finding(company_id, year, 'quality_of_earnings', 'Medium', 'Operating cash flow is significantly lower than net income, suggesting lower quality of earnings.')

    def _check_revenue_margin_drops(self, company_id: str, year: int, income_df: pd.DataFrame):
        current_revenue = self._get_field_value(income_df, company_id, year, 'revenue')
        previous_revenue = self._get_field_value(income_df, company_id, year - 1, 'revenue')
        
        if current_revenue and previous_revenue and previous_revenue > 0 and (current_revenue - previous_revenue) / previous_revenue < -0.2:
            self._add_finding(company_id, year, 'significant_revenue_decline', 'High', 'Significant revenue decline (>20% YoY).')
    
    def _check_debt_growth(self, company_id: str, year: int, balance_df: pd.DataFrame, income_df: pd.DataFrame):
        current_debt = self._get_field_value(balance_df, company_id, year, 'long_term_debt')
        previous_debt = self._get_field_value(balance_df, company_id, year - 1, 'long_term_debt')
        current_revenue = self._get_field_value(income_df, company_id, year, 'revenue')
        
        if current_debt and previous_debt and current_revenue and current_debt > previous_debt and current_revenue <= self._get_field_value(income_df, company_id, year - 1, 'revenue'):
            self._add_finding(company_id, year, 'debt_vs_revenue', 'Medium', 'Increasing debt without corresponding revenue growth.')

    def _check_cash_flow_vs_profit(self, company_id: str, year: int, income_df: pd.DataFrame, cashflow_df: pd.DataFrame):
        net_income = self._get_field_value(income_df, company_id, year, 'net_income')
        net_change_in_cash = self._get_field_value(cashflow_df, company_id, year, 'net_change_in_cash')
        
        if net_income is not None and net_change_in_cash is not None and net_income > 0 and net_change_in_cash < 0:
            self._add_finding(company_id, year, 'profit_vs_cash_flow', 'High', 'Reported net profit but had negative net cash flow for the year.')

    def _check_financial_anomalies(self, company_id: str, year: int, income_df: pd.DataFrame, balance_df: pd.DataFrame, cashflow_df: pd.DataFrame):
        # Placeholder for other anomaly checks as per previous request
        pass
    
    def _check_data_completeness(self, company_id: str, year: int, income_df: pd.DataFrame, balance_df: pd.DataFrame, cashflow_df: pd.DataFrame):
        # Placeholder for data completeness check
        pass
    
    def _add_finding(self, company_id: str, year: int, check_type: str, severity: str, details: str):
        rule_id, rule_name = QA_RULE_MAPPING.get(check_type, ('UNK', 'Unknown Rule'))
        finding = {
            'company_id': company_id,
            'year': year,
            'rule_id': rule_id,
            'rule_name': rule_name,
            'status': 'FAIL',
            'severity': severity,
            'details': details,
            'timestamp': pd.Timestamp.now()
        }
        self.findings.append(finding)
        
        if severity.lower() == 'high':
            logger.warning(f"HIGH QA Finding - {company_id} {year}: {details}")
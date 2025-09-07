// Company type
export interface Company {
  id: string;
  name: string;
}

// Financial statement types
export interface IncomeStatement {
  company_id: string;
  year: number;
  currency: string;
  revenue?: number;
  cost_of_goods_sold?: number;
  gross_profit?: number;
  operating_expenses?: number;
  operating_income?: number;
  interest_expense?: number;
  pretax_income?: number;
  income_tax?: number;
  net_income?: number;
  eps_basic?: number;
  eps_diluted?: number;
}

export interface BalanceSheet {
  company_id: string;
  year: number;
  currency: string;
  cash_and_equivalents?: number;
  accounts_receivable?: number;
  inventory?: number;
  other_current_assets?: number;
  total_current_assets?: number;
  ppe?: number;
  intangible_assets?: number;
  total_noncurrent_assets?: number;
  total_assets?: number;
  accounts_payable?: number;
  short_term_debt?: number;
  other_current_liabilities?: number;
  total_current_liabilities?: number;
  long_term_debt?: number;
  total_noncurrent_liabilities?: number;
  total_liabilities?: number;
  share_capital?: number;
  retained_earnings?: number;
  other_equity?: number;
  total_equity?: number;
}

export interface CashFlowStatement {
  company_id: string;
  year: number;
  currency: string;
  net_income?: number;
  depreciation_amortization?: number;
  working_capital_changes?: number;
  cfo?: number;
  capex?: number;
  acquisitions?: number;
  other_investing?: number;
  cfi?: number;
  debt_issued?: number;
  debt_repaid?: number;
  dividends_paid?: number;
  share_buybacks?: number;
  other_financing?: number;
  cff?: number;
  net_change_in_cash?: number;
  ending_cash_balance?: number;
}

export interface FinancialRatios {
  company_id: string;
  year: number;
  current_ratio?: number;
  quick_ratio?: number;
  debt_to_equity?: number;
  interest_coverage?: number;
  gross_margin?: number;
  net_margin?: number;
  roa?: number;
  roe?: number;
  cfo_to_net_income?: number;
  inventory_turnover?: number;
  receivables_days?: number;
}

// Combined financial data
export interface FinancialData {
  income: IncomeStatement;
  balance: BalanceSheet;
  cashflow: CashFlowStatement;
  features: FinancialRatios;
}

// Trends data
export interface TrendsData {
  income_trends: IncomeStatement[];
  balance_trends: BalanceSheet[];
  ratio_trends: FinancialRatios[];
}

// QA findings
export interface QAFinding {
  company_id: string;
  year: number;
  rule_id: string;
  rule_name: string;
  status: string;
  severity: string;
  details: string;
  timestamp: string;
}

// Search result
export interface SearchResult {
  score: number;
  company_id: string;
  year: number;
  section: string;
  page_no: string;
  text: string;
  chunk_id: string;
}

// App state
export interface AppState {
  isDataLoaded: boolean;
  companies: Company[];
  selectedCompany: Company | null;
  availableYears: number[];
  selectedYear: number | null;
  financialData: FinancialData | null;
  trendsData: TrendsData | null;
  qaFindings: QAFinding[];
  isLoading: boolean;
  error: string | null;
}

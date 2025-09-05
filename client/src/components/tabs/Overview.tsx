import React from 'react';
import { useAppContext } from '../../context/AppContext';

const Overview: React.FC = () => {
  const { state } = useAppContext();
  const { financialData, selectedCompany, selectedYear } = state;
  
  if (!financialData || !selectedCompany || !selectedYear) {
    return (
      <div className="text-center py-10">
        <p className="text-gray-600 dark:text-gray-400">
          Select a company and year to view financial overview.
        </p>
      </div>
    );
  }

  const { income, balance, cashflow, features } = financialData;

  // Debug logging
  console.log('Financial Data:', financialData);
  console.log('Selected Company:', selectedCompany);
  console.log('Selected Year:', selectedYear);

  // Format a number as currency
  const formatCurrency = (value?: number | null) => {
    if (value === undefined || value === null || isNaN(value)) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Format a number as regular number
  const formatNumber = (value?: number | null, decimals = 2) => {
    if (value === undefined || value === null || isNaN(value)) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      maximumFractionDigits: decimals,
    }).format(value);
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">
        Financial Overview - {selectedCompany.name} ({selectedYear})
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Income Statement */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 border-b pb-2">Income Statement</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Revenue</span>
              <span className="font-medium">{formatCurrency(income?.revenue)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Operating Income</span>
              <span className="font-medium">{formatCurrency(income?.operating_income)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Net Income</span>
              <span className="font-medium">{formatCurrency(income?.net_income)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Interest Expense</span>
              <span className="font-medium">{formatCurrency(income?.interest_expense)}</span>
            </div>
          </div>
        </div>

        {/* Balance Sheet */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 border-b pb-2">Balance Sheet</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Total Assets</span>
              <span className="font-medium">{formatCurrency(balance?.total_assets)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Total Equity</span>
              <span className="font-medium">{formatCurrency(balance?.total_equity)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Total Liabilities</span>
              <span className="font-medium">{formatCurrency(balance?.total_liabilities)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Cash & Equivalents</span>
              <span className="font-medium">{formatCurrency(balance?.cash_and_equivalents)}</span>
            </div>
          </div>
        </div>

        {/* Cash Flow */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 border-b pb-2">Cash Flow</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Operating Cash Flow</span>
              <span className="font-medium">{formatCurrency(cashflow?.cfo)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Investing Cash Flow</span>
              <span className="font-medium">{formatCurrency(cashflow?.cfi)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Financing Cash Flow</span>
              <span className="font-medium">{formatCurrency(cashflow?.cff)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Net Income</span>
              <span className="font-medium">{formatCurrency(cashflow?.net_income)}</span>
            </div>
          </div>
        </div>

        {/* Financial Ratios */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 border-b pb-2">Key Ratios</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Net Margin</span>
              <span className="font-medium">{formatNumber((features?.net_margin || 0) * 100, 1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Interest Coverage</span>
              <span className="font-medium">{formatNumber(features?.interest_coverage, 1)}x</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Current Ratio</span>
              <span className="font-medium">{formatNumber(features?.current_ratio, 2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">ROA</span>
              <span className="font-medium">{formatNumber((features?.roa || 0) * 100, 1)}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Overview;

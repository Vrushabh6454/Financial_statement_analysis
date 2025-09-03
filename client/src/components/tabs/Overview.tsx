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

  const { income, balance, cashflow } = financialData;

  // Format a number as currency
  const formatCurrency = (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">
        Financial Overview - {selectedCompany.name} ({selectedYear})
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Income Statement */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4 border-b pb-2">Income Statement</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Revenue</span>
              <span className="font-medium">{formatCurrency(income?.revenue)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Net Income</span>
              <span className="font-medium">{formatCurrency(income?.net_income)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Operating Income</span>
              <span className="font-medium">{formatCurrency(income?.operating_income)}</span>
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
          </div>
        </div>
      </div>
    </div>
  );
};

export default Overview;

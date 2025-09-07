import React, { useEffect, useRef } from 'react';
import { useAppContext } from '../../context/AppContext';

// Since we're using React, we would ideally use a charting library that works well with React
// For this example, we'll simulate using a charting library with canvas
const FinancialTrends: React.FC = () => {
  const { state } = useAppContext();
  const { trendsData, selectedCompany } = state;
  const chartRef = useRef<HTMLDivElement>(null);
  
  // In a real implementation, we would import and use a library like Chart.js or Recharts
  // For this example, we'll just display the data

  if (!trendsData || !selectedCompany) {
    return (
      <div className="text-center py-10">
        <p className="text-gray-600 dark:text-gray-400">
          Select a company to view financial trends.
        </p>
      </div>
    );
  }

  const { income_trends, balance_trends, ratio_trends } = trendsData;

  // Format numbers for display
  const formatNumber = (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Format as percentage
  const formatPercent = (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      maximumFractionDigits: 2,
    }).format(value);
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">
        Financial Trends - {selectedCompany.name}
      </h2>

      {/* Revenue Trend */}
      <div className="mb-8 bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Revenue Trend</h3>
        
        <div className="h-64 mb-4" ref={chartRef}>
          {/* In a real implementation, we would render a chart here */}
          <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded h-full flex items-center justify-center">
            <p className="text-gray-500 dark:text-gray-400">
              Chart would be rendered here with actual charting library
            </p>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead>
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Year</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Revenue</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Net Income</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Net Margin</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {income_trends.map((data, index) => {
                const year = data.year;
                const ratios = ratio_trends.find(r => r.year === year);
                
                return (
                  <tr key={index} className={index % 2 === 0 ? "bg-gray-50 dark:bg-gray-900/50" : ""}>
                    <td className="px-4 py-2 whitespace-nowrap">{data.year}</td>
                    <td className="px-4 py-2 text-right whitespace-nowrap">{formatNumber(data.revenue)}</td>
                    <td className="px-4 py-2 text-right whitespace-nowrap">{formatNumber(data.net_income)}</td>
                    <td className="px-4 py-2 text-right whitespace-nowrap">{formatPercent(ratios?.net_margin)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Financial Ratios */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Financial Ratios</h3>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead>
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Year</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ROA</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ROE</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Current Ratio</th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Debt to Equity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {ratio_trends.map((data, index) => (
                <tr key={index} className={index % 2 === 0 ? "bg-gray-50 dark:bg-gray-900/50" : ""}>
                  <td className="px-4 py-2 whitespace-nowrap">{data.year}</td>
                  <td className="px-4 py-2 text-right whitespace-nowrap">{formatPercent(data.roa)}</td>
                  <td className="px-4 py-2 text-right whitespace-nowrap">{formatPercent(data.roe)}</td>
                  <td className="px-4 py-2 text-right whitespace-nowrap">{formatNumber(data.current_ratio)}</td>
                  <td className="px-4 py-2 text-right whitespace-nowrap">{formatNumber(data.debt_to_equity)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default FinancialTrends;

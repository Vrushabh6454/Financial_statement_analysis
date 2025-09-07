import React from "react";
import { Link } from "react-router-dom";
import { useAppContext } from "../context/AppContext";

const Dashboard: React.FC = () => {
  const { state, selectCompany, selectYear } = useAppContext();
  const { 
    isDataLoaded, 
    companies, 
    selectedCompany, 
    availableYears, 
    selectedYear,
    isLoading
  } = state;

  const handleCompanyChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const companyId = e.target.value;
    const company = companies.find(c => c.id === companyId);
    if (company) {
      selectCompany(company);
    }
  };

  const handleYearChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const year = parseInt(e.target.value, 10);
    if (!isNaN(year)) {
      selectYear(year);
    }
  };

  return (
    <aside className="w-64 h-screen bg-gray-200 dark:bg-gray-900 p-6 flex flex-col">
      {/* Status Badge */}
      <div className="mb-6">
        {isLoading ? (
          <span className="block w-full text-center py-2 px-3 bg-blue-600 text-white rounded">
            ⏳ Loading...
          </span>
        ) : isDataLoaded ? (
          <span className="block w-full text-center py-2 px-3 bg-green-600 text-white rounded">
            ✅ Data loaded
          </span>
        ) : (
          <span className="block w-full text-center py-2 px-3 bg-yellow-600 text-white rounded">
            ⚠️ No data loaded
          </span>
        )}
      </div>

      {/* Title */}
      <h2 className="text-lg font-bold mb-6 text-gray-800 dark:text-gray-200">
        Company & Year Selection
      </h2>

      {/* Company Select */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
          Select Company
        </label>
        <select 
          className="w-full p-2 rounded bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-800 dark:text-gray-200"
          value={selectedCompany?.id || ""}
          onChange={handleCompanyChange}
          disabled={!isDataLoaded || isLoading || companies.length === 0}
        >
          {companies.length === 0 ? (
            <option value="">No companies available</option>
          ) : (
            <>
              <option value="">Select a company</option>
              {companies.map(company => (
                <option key={company.id} value={company.id}>
                  {company.name}
                </option>
              ))}
            </>
          )}
        </select>
      </div>

      {/* Year Select */}
      <div className="mb-8">
        <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
          Select Year
        </label>
        <select 
          className="w-full p-2 rounded bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-800 dark:text-gray-200"
          value={selectedYear || ""}
          onChange={handleYearChange}
          disabled={!selectedCompany || isLoading || availableYears.length === 0}
        >
          {!selectedCompany ? (
            <option value="">Select a company first</option>
          ) : availableYears.length === 0 ? (
            <option value="">No data available</option>
          ) : (
            <>
              <option value="">Select a year</option>
              {availableYears.map(year => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </>
          )}
        </select>
      </div>

      {/* Navigation Links */}
      <nav className="mt-auto space-y-3">
        <Link
          to="/"
          className="block px-3 py-2 rounded hover:bg-blue-600 hover:text-white text-gray-800 dark:text-gray-200"
        >
          Home
        </Link>
        <Link
          to="/reports"
          className="block px-3 py-2 rounded hover:bg-blue-600 hover:text-white text-gray-800 dark:text-gray-200"
        >
          Reports
        </Link>
      </nav>
    </aside>
  );
};

export default Dashboard;

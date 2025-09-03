import React from "react";
import { Link } from "react-router-dom";

const Dashboard: React.FC = () => {
  return (
    <aside className="w-64 h-screen bg-gray-200 dark:bg-gray-900 p-6 flex flex-col">
      {/* Status Badge */}
      <div className="mb-6">
        <span className="block w-full text-center py-2 px-3 bg-yellow-600 text-white rounded">
          ⚠️ No data loaded
        </span>
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
        <select className="w-full p-2 rounded bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-800 dark:text-gray-200">
          <option value="tatamotors">Tatamotors</option>
          <option value="infosys">Infosys</option>
          <option value="reliance">Reliance</option>
        </select>
      </div>

      {/* Year Select */}
      <div className="mb-8">
        <label className="block text-sm font-medium mb-2 text-gray-700 dark:text-gray-300">
          Select Year
        </label>
        <select className="w-full p-2 rounded bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 text-gray-800 dark:text-gray-200">
          <option value="2024">2024</option>
          <option value="2023">2023</option>
          <option value="2022">2022</option>
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

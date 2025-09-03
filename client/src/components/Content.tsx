import React, { useState } from "react";
import { Folder } from "lucide-react";
import { useAppContext } from "../context/AppContext";
import FileUpload from "./FileUpload";
import Chatbot from "./Chatbot";
import Overview from "./tabs/Overview";
import FinancialTrends from "./tabs/FinancialTrends";
import QAFindings from "./tabs/QAFindings";

const tabs = [
  { id: "overview", label: "Overview", icon: "📊" },
  { id: "trends", label: "Financial Trends", icon: "📈" },
  { id: "qa", label: "QA Findings", icon: "⚠️" },
  { id: "chatbot", label: "Chatbot Assistant", icon: "💬" },
];

const Content: React.FC = () => {
  const { state } = useAppContext();
  const [activeTab, setActiveTab] = useState("overview");
  const { isLoading, error } = state;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <Folder className="w-8 h-8 text-blue-500" />
        <h1 className="text-2xl md:text-3xl font-bold">
          Unified Financial Analysis Dashboard
        </h1>
      </div>

      {/* Loading and Error states */}
      {isLoading && (
        <div className="mb-4 p-3 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-lg">
          <p className="flex items-center">
            <span className="mr-2">⏳</span> Loading data...
          </p>
        </div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 rounded-lg">
          <p className="flex items-center">
            <span className="mr-2">❌</span> {error}
          </p>
        </div>
      )}

      {/* Upload Section */}
      <FileUpload />

      {/* Tabs */}
      <div className="border-b border-gray-300 dark:border-gray-700 mb-6">
        <nav className="flex space-x-6 overflow-x-auto pb-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-2 text-sm font-medium whitespace-nowrap ${
                activeTab === tab.id
                  ? "text-blue-500 border-b-2 border-blue-500"
                  : "text-gray-600 dark:text-gray-400 hover:text-blue-400"
              }`}
            >
              <span className="mr-1">{tab.icon}</span> {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-4">
        {activeTab === "overview" && <Overview />}
        {activeTab === "trends" && <FinancialTrends />}
        {activeTab === "qa" && <QAFindings />}
        {activeTab === "chatbot" && <Chatbot />}
      </div>
    </div>
  );
};

export default Content;


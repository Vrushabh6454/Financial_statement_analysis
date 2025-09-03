import React, { useState } from "react";
import { Upload, Folder } from "lucide-react"; // optional icons (install: npm i lucide-react)
import FileUpload from "./FileUpload";
import Chatbot from "./Chatbot";

const tabs = [
  { id: "overview", label: "Overview" },
  { id: "trends", label: "Financial Trends" },
  { id: "qa", label: "QA Findings" },
  { id: "banking", label: "Banking Insights" },
  { id: "chatbot", label: "Chatbot Assistant" },
  { id: "review", label: "Review Report" },
];

const Content: React.FC = () => {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <Folder className="w-8 h-8 text-blue-500" />
        <h1 className="text-2xl md:text-3xl font-bold">
          Unified Financial Analysis Dashboard
        </h1>
      </div>

      {/* Upload Section */}
      <FileUpload />

      {/* Tabs */}
      <div className="border-b border-gray-300 dark:border-gray-700 mb-6">
        <nav className="flex space-x-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-2 text-sm font-medium ${activeTab === tab.id
                ? "text-blue-500 border-b-2 border-blue-500"
                : "text-gray-600 dark:text-gray-400 hover:text-blue-400"
                }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-4">
        {activeTab === "overview" && (
          <p className="text-lg">📊 This is the Overview content.</p>
        )}
        {activeTab === "trends" && (
          <p className="text-lg">📈 Financial Trends data will appear here.</p>
        )}
        {activeTab === "qa" && (
          <p className="text-lg">✅ QA Findings will be shown here.</p>
        )}
        {activeTab === "banking" && (
          <p className="text-lg">🏦 Banking Insights will be displayed.</p>
        )}
        {activeTab === "chatbot" && (
          <p className="text-lg">{activeTab === "chatbot" && <Chatbot />}</p>
        )}
        {activeTab === "review" && (
          <p className="text-lg">📑 Review Report section.</p>
        )}
      </div>
    </div>
  );
};

export default Content;

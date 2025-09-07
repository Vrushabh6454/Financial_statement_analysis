import React, { useState } from "react";
import { useAppContext } from "../context/AppContext";
import { SearchResult } from "../types";
import api from "../services/api";

const Chatbot: React.FC = () => {
  const { state } = useAppContext();
  const { selectedCompany, selectedYear } = state;
  const [input, setInput] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async () => {
    if (!input.trim()) return;

    setIsSearching(true);
    setError(null);
    
    try {
      const searchResults = await api.search(
        input.trim(),
        selectedCompany?.id,
        selectedYear || undefined
      );
      
      setResults(searchResults);
    } catch (err) {
      console.error("Search error:", err);
      setError("Failed to perform search. Please try again.");
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <h2 className="text-2xl font-bold mb-6">
        AI-Powered Q&A from Financial Notes
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          {/* Label */}
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Enter your question:
          </label>

          {/* Input box */}
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="e.g., What are the main risk factors mentioned?"
            rows={3}
            className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 mb-4 text-gray-900 dark:text-gray-100 dark:bg-gray-900 resize-none"
          />

          {/* Button */}
          <button
            onClick={handleSend}
            disabled={isSearching || !input.trim() || !selectedCompany}
            className={`px-6 py-2 rounded-md ${
              isSearching || !input.trim() || !selectedCompany
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-red-600 hover:bg-red-700"
            } text-white`}
          >
            {isSearching ? "Searching..." : "🔍 Search"}
          </button>
          
          {!selectedCompany && (
            <p className="text-yellow-600 dark:text-yellow-400 mt-2 text-sm">
              Please select a company first.
            </p>
          )}
          
          {error && (
            <p className="text-red-600 dark:text-red-400 mt-2">
              {error}
            </p>
          )}
        </div>
        
        <div>
          <h3 className="text-lg font-semibold mb-4">Search Results</h3>
          
          {results.length === 0 ? (
            <div className="text-center py-8 bg-gray-100 dark:bg-gray-700 rounded">
              <p className="text-gray-600 dark:text-gray-400">
                {isSearching
                  ? "Searching..."
                  : "No results yet. Enter a question to search financial documents."}
              </p>
            </div>
          ) : (
            <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
              {results.map((result, index) => (
                <div
                  key={index}
                  className="bg-gray-50 dark:bg-gray-900/50 p-4 rounded border-l-4 border-blue-500"
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm font-medium text-blue-800 dark:text-blue-300">
                      {result.company_id} ({result.year}) - {result.section}
                    </span>
                    <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 px-2 py-1 rounded">
                      Score: {result.score.toFixed(2)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300">{result.text}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Chatbot;

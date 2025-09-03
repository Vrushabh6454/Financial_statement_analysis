import React, { useState } from "react";

const Chatbot: React.FC = () => {
  const [input, setInput] = useState("");

  const handleSend = async () => {
    if (!input.trim()) return;
    console.log("User Question:", input);
    setInput("");
    // Later: replace with API fetch for answers
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
      {/* Header */}
      <h2 className="text-xl font-semibold mb-4">
        AI-Powered Q&A from Financial Notes
      </h2>

      {/* Label */}
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Enter your question:
      </label>

      {/* Input box */}
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="e.g., What are the main risk factors mentioned?"
        rows={3}
        className="w-full border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 mb-4 text-gray-900 dark:text-gray-100 dark:bg-gray-900 resize-none"
      />

      {/* Button */}
      <button
        onClick={handleSend}
        className="px-6 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
      >
        🔴 Get Answer
      </button>
    </div>
  );
};

export default Chatbot;

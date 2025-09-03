import React, { useState, useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import Content from "./components/Content";

const App: React.FC = () => {
  const [theme, setTheme] = useState<"light" | "dark">("light");

  useEffect(() => {
    document.documentElement.classList.remove("light", "dark");
    document.documentElement.classList.add(theme);
  }, [theme]);

  return (
    <div className="flex min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <Dashboard />
      <div className="flex-1 p-6">
        <div className="flex justify-end mb-4">
          <button
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            className="px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600"
          >
            Toggle {theme === "light" ? "Dark" : "Light"}
          </button>
        </div>
        <Routes>
          <Route path="/" element={<Content />} />
        </Routes>
      </div>
    </div>
  );
};

export default App;

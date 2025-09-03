import React from 'react';
import { useAppContext } from '../../context/AppContext';
import { QAFinding } from '../../types';

const QAFindings: React.FC = () => {
  const { state } = useAppContext();
  const { qaFindings, selectedCompany, selectedYear } = state;
  
  if (!selectedCompany) {
    return (
      <div className="text-center py-10">
        <p className="text-gray-600 dark:text-gray-400">
          Select a company to view QA findings.
        </p>
      </div>
    );
  }

  // Group findings by severity
  const groupedFindings = {
    High: qaFindings.filter(f => f.severity.toLowerCase() === 'high'),
    Medium: qaFindings.filter(f => f.severity.toLowerCase() === 'medium'),
    Low: qaFindings.filter(f => f.severity.toLowerCase() === 'low'),
  };

  // Get severity color
  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300';
      case 'low':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300';
    }
  };

  // Get severity icon
  const getSeverityIcon = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'high':
        return '🔴';
      case 'medium':
        return '🟡';
      case 'low':
        return '🔵';
      default:
        return '⚪';
    }
  };

  const renderFindingCard = (finding: QAFinding) => (
    <div 
      key={finding.rule_id} 
      className="mb-4 p-4 bg-white dark:bg-gray-800 rounded-lg shadow"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center">
          <span className="mr-2">{getSeverityIcon(finding.severity)}</span>
          <h3 className="text-lg font-medium">{finding.rule_name}</h3>
        </div>
        <span 
          className={`px-2 py-1 text-xs font-medium rounded ${getSeverityColor(finding.severity)}`}
        >
          {finding.severity}
        </span>
      </div>
      <p className="mt-2 text-gray-600 dark:text-gray-400">{finding.details}</p>
      <div className="mt-4 text-sm text-gray-500">
        <span className="mr-4">Rule ID: {finding.rule_id}</span>
        <span>Year: {finding.year}</span>
      </div>
    </div>
  );

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">
        Quality Assurance Findings - {selectedCompany.name}
        {selectedYear && ` (${selectedYear})`}
      </h2>

      {qaFindings.length === 0 ? (
        <div className="text-center py-10 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <p className="text-green-600 dark:text-green-400">
            No QA issues found. All checks passed successfully!
          </p>
        </div>
      ) : (
        <div>
          {/* High severity findings */}
          {groupedFindings.High.length > 0 && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <span className="mr-2">🔴</span>
                Critical Findings
              </h3>
              {groupedFindings.High.map(renderFindingCard)}
            </div>
          )}

          {/* Medium severity findings */}
          {groupedFindings.Medium.length > 0 && (
            <div className="mb-8">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <span className="mr-2">🟡</span>
                Warning Findings
              </h3>
              {groupedFindings.Medium.map(renderFindingCard)}
            </div>
          )}

          {/* Low severity findings */}
          {groupedFindings.Low.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <span className="mr-2">🔵</span>
                Informational Findings
              </h3>
              {groupedFindings.Low.map(renderFindingCard)}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default QAFindings;

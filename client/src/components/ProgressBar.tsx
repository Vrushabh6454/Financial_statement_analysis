import React from 'react';

interface ProgressBarProps {
  progress: number;
  status: string;
  completed: boolean;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ progress, status, completed }) => {
  return (
    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-lg overflow-hidden">
      <div className="px-4 py-3">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {status}
          </span>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {progress}%
          </span>
        </div>
        
        <div className="w-full bg-gray-300 dark:bg-gray-600 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all duration-300 ease-out ${
              completed && progress === 100
                ? 'bg-green-600'
                : 'bg-blue-600'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
        
        {completed && (
          <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
            {progress === 100 && status.includes('successfully') 
              ? '✅ Processing completed successfully!' 
              : progress === 100 && status.includes('Error')
              ? '❌ Processing failed'
              : '⚠️ Processing completed with warnings'
            }
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressBar;

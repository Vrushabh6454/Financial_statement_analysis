import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { AppState, Company, FinancialData, TrendsData, QAFinding } from '../types';
import api from '../services/api';

// Initial app state
const initialState: AppState = {
  isDataLoaded: false,
  companies: [],
  selectedCompany: null,
  availableYears: [],
  selectedYear: null,
  financialData: null,
  trendsData: null,
  qaFindings: [],
  isLoading: false,
  error: null,
};

// Create context
interface AppContextType {
  state: AppState;
  loadCompanies: () => Promise<void>;
  selectCompany: (company: Company) => Promise<void>;
  selectYear: (year: number) => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// Provider component
export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AppState>(initialState);

  // Load companies on mount if data exists
  useEffect(() => {
    const checkForData = async () => {
      try {
        console.log('Checking for initial data...');
        const companies = await api.getCompanies();
        console.log('Found companies:', companies);
        if (companies.length > 0) {
          setState(prev => ({
            ...prev,
            isDataLoaded: true,
            companies
          }));
          console.log('Data loaded successfully');
        }
      } catch (error) {
        console.log('No data available yet:', error);
      }
    };

    checkForData();
  }, []);

  // Load companies
  const loadCompanies = async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));
    try {
      const companies = await api.getCompanies();
      setState(prev => ({
        ...prev,
        companies,
        isDataLoaded: companies.length > 0,
        isLoading: false
      }));
    } catch (error) {
      console.error('Failed to load companies', error);
      setState(prev => ({
        ...prev,
        error: 'Failed to load companies',
        isLoading: false
      }));
    }
  };

  // Select company
  const selectCompany = async (company: Company) => {
    console.log('Selecting company:', company);
    setState(prev => ({ 
      ...prev, 
      isLoading: true, 
      error: null,
      selectedCompany: company,
      selectedYear: null,
      availableYears: [],
      financialData: null,
      trendsData: null,
      qaFindings: []
    }));

    try {
      console.log('Fetching years and trends for company:', company.id);
      const [years, trendsData] = await Promise.all([
        api.getYears(company.id),
        api.getTrends(company.id)
      ]);

      console.log('Received years:', years);
      console.log('Received trends:', trendsData);

      setState(prev => ({
        ...prev,
        availableYears: years,
        trendsData,
        isLoading: false
      }));

      // If years available, select the most recent by default
      if (years.length > 0) {
        const mostRecentYear = Math.max(...years);
        console.log('Auto-selecting most recent year:', mostRecentYear);
        
        // Load financial data for the most recent year
        setState(prev => ({ 
          ...prev, 
          isLoading: true,
          selectedYear: mostRecentYear
        }));

        try {
          console.log('Fetching financial data for:', company.id, mostRecentYear);
          const [financialData, qaFindings] = await Promise.all([
            api.getFinancialData(company.id, mostRecentYear),
            api.getQAFindings(company.id, mostRecentYear)
          ]);

          console.log('Received financial data:', financialData);
          console.log('Received QA findings:', qaFindings);

          setState(prev => ({
            ...prev,
            financialData,
            qaFindings,
            isLoading: false
          }));
        } catch (yearError) {
          console.error('Failed to load year data', yearError);
          const errorMessage = yearError instanceof Error ? yearError.message : 'Failed to load year data';
          setState(prev => ({
            ...prev,
            error: errorMessage,
            isLoading: false
          }));
        }
      }
    } catch (error) {
      console.error('Failed to load company data', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to load company data';
      setState(prev => ({
        ...prev,
        error: errorMessage,
        isLoading: false
      }));
    }
  };

  // Select year
  const selectYear = async (year: number) => {
    if (!state.selectedCompany) return;

    setState(prev => ({ 
      ...prev, 
      isLoading: true, 
      error: null,
      selectedYear: year
    }));

    try {
      const [financialData, qaFindings] = await Promise.all([
        api.getFinancialData(state.selectedCompany.id, year),
        api.getQAFindings(state.selectedCompany.id, year)
      ]);

      setState(prev => ({
        ...prev,
        financialData,
        qaFindings,
        isLoading: false
      }));
    } catch (error) {
      console.error('Failed to load year data', error);
      setState(prev => ({
        ...prev,
        error: 'Failed to load year data',
        isLoading: false
      }));
    }
  };

  // Upload file
  const uploadFile = async (file: File) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await api.uploadFile(file);
      
      // Check if there's a warning in the response
      if (response.warning) {
        setState(prev => ({
          ...prev,
          error: response.warning || null,
          isLoading: false
        }));
        return;
      }
      
      await loadCompanies();
    } catch (error) {
      console.error('Failed to upload file', error);
      let errorMessage = 'Failed to upload and process file';
      if (error instanceof Error) {
        errorMessage = error.message;
      }
      setState(prev => ({
        ...prev,
        error: errorMessage,
        isLoading: false
      }));
    }
  };

  return (
    <AppContext.Provider
      value={{
        state,
        loadCompanies,
        selectCompany,
        selectYear,
        uploadFile
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

// Custom hook for using the app context
export const useAppContext = (): AppContextType => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

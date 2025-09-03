import { FinancialData, Company, TrendsData, QAFinding, SearchResult } from '../types';

const API_URL = 'http://localhost:5000/api';

export const api = {
  // Upload PDF file
  uploadFile: async (file: File): Promise<{ message?: string; warning?: string; filename: string }> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok && response.status !== 202) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to upload file');
    }

    return response.json();
  },

  // Get list of companies
  getCompanies: async (): Promise<Company[]> => {
    const response = await fetch(`${API_URL}/companies`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch companies');
    }

    const data = await response.json();
    return data.companies;
  },

  // Get available years for a company
  getYears: async (companyId: string): Promise<number[]> => {
    const response = await fetch(`${API_URL}/years/${companyId}`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch years');
    }

    const data = await response.json();
    return data.years;
  },

  // Get financial data for a specific company and year
  getFinancialData: async (companyId: string, year: number): Promise<FinancialData> => {
    const response = await fetch(`${API_URL}/financial-data/${companyId}/${year}`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch financial data');
    }

    return response.json();
  },

  // Get trends data for a company
  getTrends: async (companyId: string): Promise<TrendsData> => {
    const response = await fetch(`${API_URL}/trends/${companyId}`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch trends');
    }

    return response.json();
  },

  // Get QA findings for a company
  getQAFindings: async (companyId: string, year?: number): Promise<QAFinding[]> => {
    const url = year 
      ? `${API_URL}/qa-findings/${companyId}?year=${year}`
      : `${API_URL}/qa-findings/${companyId}`;
      
    const response = await fetch(url);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to fetch QA findings');
    }

    const data = await response.json();
    return data.findings;
  },

  // Search through financial notes
  search: async (query: string, companyId?: string, year?: number): Promise<SearchResult[]> => {
    const response = await fetch(`${API_URL}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        company_id: companyId,
        year,
      }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to perform search');
    }

    const data = await response.json();
    return data.results;
  },
};

export default api;

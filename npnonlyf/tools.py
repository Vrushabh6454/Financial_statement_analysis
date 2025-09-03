# tools.py

from crewai.tools import BaseTool
from typing import Type, ClassVar, Dict
import pandas as pd
from npnonlyf.embeddings import FinancialEmbeddingsManager
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the embeddings manager once
try:
    embeddings_manager = FinancialEmbeddingsManager(index_path='data/embeddings')
    if not embeddings_manager.load_index_and_metadata():
        logger.warning("Embeddings not loaded. Semantic search tool may not function correctly.")
        embeddings_manager = None
except Exception as e:
    logger.error(f"Failed to initialize embeddings manager: {e}")
    embeddings_manager = None

class SemanticSearchTool(BaseTool):
    """
    A custom tool that performs a semantic search on financial notes using FAISS embeddings.
    """
    name: str = "Semantic Search Tool"
    description: str = (
        "Useful for searching and retrieving relevant information from a vector database of financial notes. "
        "The input to this tool MUST be a simple, raw string search query. "
        "Example input: 'What are the main risk factors mentioned?'"
    )

    def _run(self, query: str) -> str:
        """
        Executes a semantic search and returns the top results.
        
        Args:
            query (str): The search query.
            
        Returns:
            str: A formatted string containing the top search results with metadata.
        """
        if not embeddings_manager:
            return "Embeddings database not available."
        
        try:
            results = embeddings_manager.semantic_search(query=query, top_k=5)
            
            if not results:
                return "No relevant information found for the query."
            
            formatted_results = []
            for i, res in enumerate(results):
                formatted_results.append(
                    f"Source {i+1} [Company: {res['company_id']}, Year: {res['year']}, Section: {res['section']}]\n"
                    f"Text: {res['text']}\n"
                )
            
            return "\n\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            return f"An error occurred while performing the search: {e}"


class FinancialDataTool(BaseTool):
    """
    A custom tool for retrieving structured financial data (e.g., ratios, values) from DataFrames.
    """
    name: str = "Financial Data Tool"
    description: str = (
        "Useful for fetching specific structured financial data points "
        "from the income, balance, cashflow, and features DataFrames. "
        "The input MUST be a JSON string with the following keys: 'company_id' (string), 'year' (int), 'statement_type' (string), and 'field' (string). "
        "Example input: '{\"company_id\": \"uuid-123\", \"year\": 2023, \"statement_type\": \"income\", \"field\": \"revenue\"}'"
    )
    
    loaded_data: ClassVar[Dict] = {}

    def _run(self, query: str) -> str:
        """
        Retrieves a specific data point from the loaded financial data.
        """
        try:
            params = json.loads(query)
            company_id = params.get('company_id')
            year = params.get('year')
            statement_type = params.get('statement_type')
            field = params.get('field')

            if not all([company_id, year, statement_type, field]):
                return "Error: Missing required parameters (company_id, year, statement_type, field)."

            if not self.loaded_data:
                return "Error: Financial data has not been loaded into the tool."

            df_key = None
            if statement_type == 'income':
                df_key = 'income'
            elif statement_type == 'balance':
                df_key = 'balance'
            elif statement_type == 'cashflow':
                df_key = 'cashflow'
            elif statement_type == 'features':
                df_key = 'features'

            if df_key and df_key in self.loaded_data:
                df = self.loaded_data[df_key]
                if df.empty:
                    return f"Error: {statement_type} data is empty."
                
                # Filter by company_id and year first
                data_row = df[(df['company_id'] == company_id) & (df['year'] == year)]

                if not data_row.empty:
                    # Check if the requested field exists in the DataFrame
                    if field in data_row.columns:
                        value = data_row.iloc[0][field]
                        if pd.isna(value):
                            return f"Value for '{field}' not available for {company_id} in {year}."
                        return f"Found {field} for {company_id} in {year}: {value}"
                    else:
                        return f"Data not found for field: {field} in {statement_type}."
                else:
                    return f"Data not found for company: {company_id}, year: {year} in {statement_type}."

            return f"Error: Invalid statement_type '{statement_type}' or data not found."

        except json.JSONDecodeError:
            return "Error: Invalid JSON input format. The input MUST be a JSON string like: {'company_id': 'uuid', 'year': 2023, 'statement_type': 'income', 'field': 'revenue'}"
        except Exception as e:
            logger.error(f"Error in FinancialDataTool: {e}")
            return f"An unexpected error occurred: {e}"
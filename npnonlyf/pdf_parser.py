"""
PDF parsing module for extracting financial statement data and text.
"""

import os
import re
import pandas as pd
import numpy as np
import pdfplumber
import pytesseract
from tika import parser
import io  
from PIL import Image
from typing import Dict, List, Tuple, Optional, Any
import logging
import uuid
import pymupdf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFParser:
    """
    Advanced PDF parser for financial documents with OCR capabilities.
    """
    
    def __init__(self, ocr_enabled: bool = True):
        """
        Initialize PDF parser.
        
        Args:
            ocr_enabled: Whether to enable OCR for scanned PDFs
        """
        self.ocr_enabled = ocr_enabled
        
    def extract_pdf_content(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract both structured tables and unstructured text from PDF.
        """
        try:
            logger.info(f"Processing PDF: {pdf_path}")
            
            result = {
                'tables': [],
                'text': '',
                'company': self._extract_company_name(pdf_path),
                'year': self._extract_year(pdf_path),
                'pages': 0
            }
            
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    result['pages'] = len(pdf.pages)
                    full_text = []
                    
                    for i, page in enumerate(pdf.pages):
                        page_text = page.extract_text()
                        if page_text:
                            full_text.append(page_text)
                            
                            tables = page.extract_tables()
                            for table in tables:
                                if self._is_financial_table(table):
                                    processed_table = self._process_table(table, result['company'], result['year'])
                                    if processed_table:
                                        result['tables'].append(processed_table)
                    
                    result['text'] = '\n\n'.join(full_text)
                    
            except Exception as e:
                logger.warning(f"pdfplumber failed for {pdf_path}: {e}")
                
                try:
                    parsed = parser.from_file(pdf_path)
                    if parsed and parsed.get('content'):
                        result['text'] = parsed['content']
                        result['tables'] = self._extract_tables_from_text(
                            result['text'], result['company'], result['year']
                        )
                except Exception as e2:
                    logger.error(f"Tika parser also failed for {pdf_path}: {e2}")
                    
                    if self.ocr_enabled:
                        result = self._ocr_fallback(pdf_path, result)
            
            logger.info(f"Extracted {len(result['tables'])} tables and {len(result['text'])} characters of text")
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return {'tables': [], 'text': '', 'company': 'Unknown', 'year': 0, 'pages': 0}
    
    def _extract_company_name(self, pdf_path: str) -> str:
        """
        Extract company name from filename or PDF content.
        """
        filename = os.path.basename(pdf_path)
        
        patterns = [
            r'([A-Za-z\s&.-]+)_annual_report',
            r'([A-Za-z\s&.-]+)_10k',
            r'([A-Za-z\s&.-]+)_annual',
            r'([A-Za-z\s&.-]+)-\d{4}',
            r'^([A-Za-z\s&.-]+)_',
            r'([A-Za-z\s&.-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                company_name = re.sub(r'[\s\W_]+$', '', match.group(1).replace('-', ' ')).strip().title()
                return company_name
        
        return os.path.splitext(filename)[0].replace('_', ' ').title()
    
    def _extract_year(self, pdf_path: str) -> int:
        """
        Extract year from filename.
        """
        filename = os.path.basename(pdf_path)
        
        year_match = re.search(r'20(\d{2})[-_]?(\d{2})?', filename)
        if year_match:
            return int('20' + year_match.group(1))
        
        year_match = re.search(r'20\d{2}', filename)
        if year_match:
            return int(year_match.group())
        
        return 2023
    
    def _is_financial_table(self, table: List[List[str]]) -> bool:
        """
        Determine if a table contains financial statement data.
        """
        if not table or len(table) < 3:
            return False
        
        table_text = ' '.join([' '.join(row) for row in table if row])
        table_text = table_text.lower()
        
        financial_keywords = [
            'revenue', 'sales', 'income', 'profit', 'loss', 'assets', 'liabilities',
            'equity', 'cash', 'expenses', 'cost', 'margin', 'earnings', 'ebit', 'ebitda',
            'balance sheet', 'income statement', 'cash flow', 'statement of operations',
            'consolidated', 'financial', 'statement', 'annual report', 'fiscal year',
            'net', 'total', 'operating', 'gross', 'debt', 'depreciation'
        ]
        
        currency_indicators = ['$', '€', '£', '¥', 'thousand', 'million', 'billion', 'USD', 'EUR', 'GBP', 'JPY']
        
        # Increase sensitivity by checking if any of these terms are in the table
        keyword_count = sum(1 for keyword in financial_keywords if keyword in table_text)
        currency_count = sum(1 for indicator in currency_indicators if indicator in table_text)
        
        # More lenient check - return true if we have at least one financial keyword
        return keyword_count >= 1 or currency_count >= 1
    
    def _process_table(self, table: List[List[str]], company: str, year: int) -> Optional[Dict]:
        """
        Process a raw table into structured financial data.
        """
        if not table:
            return None
        
        try:
            # Handle potential None values in the table by converting to string
            df = pd.DataFrame([[str(cell) if cell is not None else '' for cell in row] for row in table])
            df = df.dropna(how='all').fillna('')
            
            if df.empty or len(df) < 2:
                return None
            
            # Look at entire table text for statement type identification
            full_table_text = ' '.join([' '.join(row) for row in df.values.astype(str)])
            table_text = ' '.join(df.iloc[0].astype(str)).lower()
            
            # Try to identify the statement type from both the header and full table
            statement_type = self._identify_statement_type(table_text)
            if not statement_type:
                statement_type = self._identify_statement_type(full_table_text.lower())
            
            # As fallback, if table has numeric values, consider it an income statement
            if not statement_type:
                has_numeric = any(self._clean_numeric_value(str(cell)) is not None for row in table for cell in row if cell)
                if has_numeric:
                    statement_type = 'income'
                    
            if not statement_type:
                return None
            
            rows = []
            for _, row in df.iterrows():
                row_data = [str(cell).strip() for cell in row if str(cell).strip()]
                if len(row_data) >= 2:
                    field_name = row_data[0]
                    values = row_data[1:]
                    
                    for i, value in enumerate(values):
                        clean_value = self._clean_numeric_value(value)
                        if clean_value is not None:
                            rows.append({
                                'company': company,
                                'year': year + i if len(values) > 1 else year,
                                'statement_type': statement_type,
                                'field': field_name,
                                'value': clean_value
                            })
            
            if not rows:
                return None
                
            return {
                'statement_type': statement_type,
                'data': rows,
                'raw_table': table
            }
            
        except Exception as e:
            logger.warning(f"Error processing table: {e}")
            return None
    
    def _identify_statement_type(self, text: str) -> Optional[str]:
        """
        Identify the type of financial statement from table text.
        """
        text = text.lower()
        
        # Balance sheet indicators
        balance_keywords = ['balance sheet', 'statement of financial position', 'assets', 'liabilities', 
                          'equity', 'total assets', 'total liabilities', 'current assets',
                          'non-current assets', 'stockholders equity', 'shareholders equity']
                          
        # Income statement indicators  
        income_keywords = ['income statement', 'statement of operations', 'profit', 'revenue',
                         'net income', 'earnings', 'ebitda', 'operating income', 'gross profit',
                         'statement of earnings', 'consolidated statements of operations',
                         'sales', 'expenses', 'loss']
                         
        # Cash flow indicators
        cashflow_keywords = ['cash flow', 'statement of cash flows', 'operating activities',
                           'investing activities', 'financing activities', 'cash and cash equivalents']
        
        # Check each type with more keywords
        if any(keyword in text for keyword in balance_keywords):
            return 'balance'
        elif any(keyword in text for keyword in income_keywords):
            return 'income'
        elif any(keyword in text for keyword in cashflow_keywords):
            return 'cashflow'
        
        # Last resort - try to guess based on specific terms
        if 'total' in text and ('assets' in text or 'liabilities' in text):
            return 'balance'
        elif ('revenue' in text or 'sales' in text) and ('net' in text or 'income' in text):
            return 'income'
        elif 'cash' in text and ('flow' in text or 'activities' in text):
            return 'cashflow'
        
        return None
    
    def _extract_tables_from_text(self, text: str, company: str, year: int) -> List[Dict]:
        """
        Extract financial data from unstructured text using regex patterns.
        """
        tables = []
        
        patterns = {
            'income': [
                r'revenue[\s\$]*([0-9,.]+)',
                r'net income[\s\$]*([0-9,.]+)',
                r'gross profit[\s\$]*([0-9,.]+)',
                r'sales[\s\$]*([0-9,.]+)',
                r'total revenue[\s\$]*([0-9,.]+)',
                r'operating income[\s\$]*([0-9,.]+)',
                r'earnings[\s\$]*([0-9,.]+)',
                r'ebitda[\s\$]*([0-9,.]+)'
            ],
            'balance': [
                r'total assets[\s\$]*([0-9,.]+)',
                r'cash[\s\$]*([0-9,.]+)',
                r'total liabilities[\s\$]*([0-9,.]+)',
                r'current assets[\s\$]*([0-9,.]+)',
                r'total equity[\s\$]*([0-9,.]+)',
                r'shareholders equity[\s\$]*([0-9,.]+)',
                r'stockholders equity[\s\$]*([0-9,.]+)',
                r'long[\s-]*term debt[\s\$]*([0-9,.]+)'
            ],
            'cashflow': [
                r'operating activities[\s\$]*([0-9,.]+)',
                r'investing activities[\s\$]*([0-9,.]+)',
                r'financing activities[\s\$]*([0-9,.]+)',
                r'net cash[\s\$]*([0-9,.]+)',
                r'cash flows[\s\$]*([0-9,.]+)',
                r'cash and cash equivalents[\s\$]*([0-9,.]+)',
                r'cash provided by[\s\$]*([0-9,.]+)'
            ]
        }
        
        for statement_type, type_patterns in patterns.items():
            rows = []
            for pattern in type_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    field_name = pattern.split('[')[0].strip()
                    value = self._clean_numeric_value(match.group(1))
                    if value is not None:
                        rows.append({
                            'company': company,
                            'year': year,
                            'statement_type': statement_type,
                            'field': field_name,
                            'value': value
                        })
            
            if rows:
                tables.append({
                    'statement_type': statement_type,
                    'data': rows,
                    'raw_table': None
                })
        
        return tables
    
    def _ocr_fallback(self, pdf_path: str, result: Dict) -> Dict:
        """
        OCR fallback for scanned PDFs.
        """
        try:
            logger.info(f"Attempting OCR for {pdf_path}")
            
            # Use tika parser as a fallback if PyMuPDF/fitz fails
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(pdf_path)
                ocr_text = []
                
                for page_num in range(min(doc.page_count, 10)):
                    page = doc[page_num]
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("ppm")
                    
                    try:
                        ocr_result = pytesseract.image_to_string(Image.open(io.BytesIO(img_data)))
                        ocr_text.append(ocr_result)
                    except Exception as e:
                        logger.error(f"PyTesseract OCR failed on page {page_num}: {e}")
                
                doc.close()
                
                if ocr_text:
                    result['text'] = '\n\n'.join(ocr_text)
                
            except Exception as e:
                logger.error(f"PyMuPDF processing failed: {e}")
                
                # Fallback to tika parser
                try:
                    parsed = parser.from_file(pdf_path)
                    if parsed and parsed.get('content'):
                        result['text'] = parsed['content']
                except Exception as e2:
                    logger.error(f"Tika parser also failed: {e2}")
            
            # Try to extract tables from any text we got
            if result.get('text'):
                result['tables'] = self._extract_tables_from_text(
                    result['text'], result['company'], result['year']
                )
                logger.info(f"OCR completed for {pdf_path}")
            
        except Exception as e:
            logger.error(f"All OCR methods failed for {pdf_path}: {e}")
        
        return result
    
    def extract_notes_text(self, pdf_content: Dict) -> List[Dict]:
        """
        Extract and structure notes and MD&A text for embeddings.
        """
        text = pdf_content.get('text', '')
        company = pdf_content.get('company', 'Unknown')
        year = pdf_content.get('year', 0)
        
        if not text:
            return []
        
        chunks = []
        
        section_patterns = [
            r'notes to.*financial statements',
            r'management.?s discussion and analysis',
            r'md&a',
            r'risk factors',
            r'business overview',
            r'critical accounting',
            r'market risk',
            r'liquidity',
            r'capital resources'
        ]
        
        sections = []
        for pattern in section_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                sections.append({
                    'start': match.start(),
                    'title': match.group(),
                    'pattern': pattern
                })
        
        sections.sort(key=lambda x: x['start'])
        
        if sections:
            for i, section in enumerate(sections):
                start_pos = section['start']
                end_pos = sections[i + 1]['start'] if i + 1 < len(sections) else len(text)
                
                section_text = text[start_pos:end_pos].strip()
                
                if len(section_text) > 1000:
                    paragraphs = re.split(r'\n\s*\n', section_text)
                    for j, paragraph in enumerate(paragraphs):
                        if len(paragraph.strip()) > 50:
                            chunks.append({
                                'company': company,
                                'year': year,
                                'section': section['title'],
                                'chunk_id': f"{company}_{year}_{i}_{j}",
                                'text': paragraph.strip(),
                                'length': len(paragraph)
                            })
                else:
                    chunks.append({
                        'company': company,
                        'year': year,
                        'section': section['title'],
                        'chunk_id': f"{company}_{year}_{i}_0",
                        'text': section_text,
                        'length': len(section_text)
                    })
        else:
            paragraphs = re.split(r'\n\s*\n', text)
            for i, paragraph in enumerate(paragraphs):
                if len(paragraph.strip()) > 100:
                    chunks.append({
                        'company': company,
                        'year': year,
                        'section': 'General',
                        'chunk_id': f"{company}_{year}_general_{i}",
                        'text': paragraph.strip(),
                        'length': len(paragraph)
                    })
        
        return chunks

    def _clean_numeric_value(self, value: Any) -> Optional[float]:
        """
        Clean and convert text values to numeric values.
        
        This method is now a part of the class.
        """
        if pd.isna(value) or value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if not isinstance(value, str):
            value = str(value)
        
        value = value.replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
        value = value.replace('%', '').strip()
        
        if value.startswith('-') and value.endswith(''):
            value = '-' + value[1:-1] if len(value) > 2 else value
        
        numeric_match = re.search(r'-?\d+(?:\.\d+)?', value)
        if numeric_match:
            try:
                return float(numeric_match.group())
            except ValueError:
                return None
        
        return None
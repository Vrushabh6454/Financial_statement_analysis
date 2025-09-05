"""
Enhanced PDF parsing module with comprehensive regex patterns and multi-parser support.
"""

import os
import re
import pandas as pd
import pytesseract
import io
from PIL import Image
from typing import Dict, List, Tuple, Optional, Any
import logging
import uuid
import pymupdf
import warnings

# Try to import tika, but make it optional
try:
    from tika import parser
    TIKA_AVAILABLE = True
    # Suppress Tika warnings
    warnings.filterwarnings('ignore', category=UserWarning, message='Tika server is not running.*')
except ImportError:
    TIKA_AVAILABLE = False
    parser = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Comprehensive Financial Statement Regex Patterns
COMPREHENSIVE_FINANCIAL_PATTERNS = {
    'income': {
        'revenue': [
            r'(?:revenue|sales|turnover|net sales|total revenue|operating revenue|net interest income|total sales|gross sales|sales revenue|operating sales)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)',
            r'(?:total|net)?\s*(?:revenue|sales)(?:\s+and\s+other\s+income)?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'cost_of_goods_sold': [
            r'(?:cost\s+of\s+(?:revenue|sales|goods\s+sold)|cogs|cost\s+of\s+products\s+sold|direct\s+costs|product\s+costs|manufacturing\s+costs)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'gross_profit': [
            r'(?:gross\s+(?:profit|income|margin))(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'operating_expenses': [
            r'(?:operating\s+(?:expenses|costs)|total\s+operating\s+expenses|selling\s+general\s+administrative|sg&a|sga|administrative\s+expenses)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'operating_income': [
            r'(?:operating\s+(?:income|profit)|ebit|earnings\s+before\s+interest\s+and\s+taxes|income\s+from\s+operations|operating\s+earnings)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'interest_expense': [
            r'(?:interest\s+(?:expense|paid)|financial\s+costs|interest\s+and\s+similar\s+charges|borrowing\s+costs|finance\s+costs)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'pretax_income': [
            r'(?:pretax\s+(?:income|earnings)|income\s+before\s+(?:tax|income\s+taxes)|earnings\s+before\s+tax|profit\s+before\s+tax)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'income_tax': [
            r'(?:tax\s+expense|income\s+tax(?:\s+expense)?|provision\s+for\s+taxes|tax\s+provision|current\s+tax|deferred\s+tax)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'net_income': [
            r'(?:net\s+(?:income|profit|earnings)|profit\s+(?:after\s+tax|for\s+the\s+period|attributable)|comprehensive\s+income)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)',
            r'(?:earnings|profit)(?:\s+for\s+the\s+(?:year|period))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'eps_basic': [
            r'(?:(?:basic\s+)?earnings\s+per\s+share|(?:basic\s+)?eps)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'eps_diluted': [
            r'(?:diluted\s+(?:eps|earnings\s+per\s+share))(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ]
    },
    
    'balance': {
        'cash_and_equivalents': [
            r'(?:cash(?:\s+and\s+(?:cash\s+)?equivalents)?|cash\s+at\s+bank|bank\s+balances|cash\s+and\s+short\s+term\s+investments)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'accounts_receivable': [
            r'(?:(?:accounts|trade)\s+(?:receivables?|debtors)|customer\s+receivables?|amounts\s+receivable)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'inventory': [
            r'(?:inventor(?:y|ies)|stock|finished\s+goods|raw\s+materials)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'other_current_assets': [
            r'(?:other\s+current\s+assets|prepaid\s+expenses|other\s+receivables?)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'total_current_assets': [
            r'(?:(?:total\s+)?current\s+assets)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'ppe': [
            r'(?:property(?:,?\s+plant\s+(?:and\s+)?equipment|plant\s+equipment)|ppe|fixed\s+assets|tangible\s+assets|buildings?\s+and\s+equipment)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'intangible_assets': [
            r'(?:(?:goodwill(?:\s+and\s+intangible\s+assets)?)|intangible\s+assets|intellectual\s+property|patents?|trademarks?)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'total_noncurrent_assets': [
            r'(?:(?:total\s+)?(?:noncurrent|non[\s\-]?current)\s+assets)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'total_assets': [
            r'(?:total\s+assets|assets)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'accounts_payable': [
            r'(?:(?:accounts|trade)\s+(?:payables?|creditors)|amounts\s+payable|supplier\s+payables?)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'short_term_debt': [
            r'(?:short[\s\-]?term\s+(?:debt|borrowings?|loans?)|current\s+(?:debt|borrowings?)|current\s+portion\s+of\s+debt)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'other_current_liabilities': [
            r'(?:other\s+current\s+liabilities|accrued\s+(?:expenses|liabilities)|other\s+payables?|provisions?)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'total_current_liabilities': [
            r'(?:(?:total\s+)?current\s+liabilities)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'long_term_debt': [
            r'(?:long[\s\-]?term\s+(?:debt|liabilities|borrowings?)|(?:non[\s\-]?current\s+liabilities)|bonds?\s+payable|notes?\s+payable)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'total_noncurrent_liabilities': [
            r'(?:total\s+(?:noncurrent|non[\s\-]?current)\s+liabilities)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'total_liabilities': [
            r'(?:total\s+liabilities|liabilities)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'share_capital': [
            r'(?:share\s+capital|(?:common|capital)\s+stock|additional\s+paid[\s\-]?in\s+capital|ordinary\s+shares?|equity\s+shares?)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'retained_earnings': [
            r'(?:retained\s+(?:earnings|profit)|accumulated\s+(?:earnings|profit)|(?:profit\s+)?reserves?)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'other_equity': [
            r'(?:accumulated\s+other\s+comprehensive\s+income|other\s+(?:equity|reserves?)|translation\s+reserves?|revaluation\s+reserves?)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'total_equity': [
            r'(?:(?:shareholders?|stockholders?|owners)\s+(?:equity|funds)|total\s+equity|net\s+worth)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ]
    },
    
    'cashflow': {
        'net_income': [
            r'(?:net\s+(?:income|earnings)|profit\s+for\s+the\s+period)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'depreciation_amortization': [
            r'(?:depreciation(?:\s+and\s+amortization)?|amortization|depreciation\s+expense|amortisation)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'working_capital_changes': [
            r'(?:(?:changes?\s+in\s+)?working\s+capital(?:\s+changes?|\s+adjustments)?|changes?\s+in\s+operating\s+assets)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'cfo': [
            r'(?:(?:net\s+)?cash\s+(?:from|generated\s+from)\s+operating\s+activities|operating\s+cash\s+flow|cfo|net\s+cash\s+from\s+operations)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'capex': [
            r'(?:capital\s+(?:expenditures?|investments?)|capex|purchase\s+of\s+(?:ppe|property)|additions\s+to\s+property\s+plant\s+equipment)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'acquisitions': [
            r'(?:(?:business\s+)?acquisitions?|purchase\s+of\s+subsidiaries)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'other_investing': [
            r'(?:other\s+(?:investing|investment)\s+activities)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'cfi': [
            r'(?:(?:net\s+)?cash\s+(?:from|used\s+in)\s+investing\s+activities|investing\s+cash\s+flow|cfi|net\s+cash\s+from\s+investing)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'debt_issued': [
            r'(?:debt\s+issued|proceeds\s+from\s+debt|borrowings?|loans?\s+received)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'debt_repaid': [
            r'(?:debt\s+(?:repaid|payments?)|repayment\s+of\s+debt|loan\s+repayments?)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'dividends_paid': [
            r'(?:dividends?\s+(?:paid|payments?)|distributions?)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'share_buybacks': [
            r'(?:share\s+(?:buybacks?|repurchases?)|repurchase\s+of\s+common\s+stock|treasury\s+stock\s+purchases?)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'other_financing': [
            r'(?:other\s+(?:financing|finance)\s+activities)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'cff': [
            r'(?:(?:net\s+)?cash\s+(?:from|used\s+in)\s+financing\s+activities|financing\s+cash\s+flow|cff|net\s+cash\s+from\s+financing)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'net_change_in_cash': [
            r'(?:net\s+change\s+in\s+cash|change\s+in\s+cash|net\s+cash\s+flow|(?:increase|decrease)\s+in\s+cash)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ],
        'ending_cash_balance': [
            r'(?:(?:ending|closing)\s+cash\s+balance|cash\s+at\s+(?:end\s+of\s+)?period(?:\s+end)?)(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
        ]
    }
}

class PDFParser:
    """Enhanced PDF parser with comprehensive extraction capabilities."""
    
    def __init__(self, parser_engine: str = 'pymupdf'):
        self.parser_engine = parser_engine.lower()
        if self.parser_engine not in ['pymupdf', 'tesseract', 'tika']:
            raise ValueError(f"Invalid parser engine: {parser_engine}")

    def extract_pdf_content(self, pdf_path: str) -> Dict[str, Any]:
        """Main extraction method that routes to specific parsers."""
        logger.info(f"Processing PDF: {pdf_path} with engine: {self.parser_engine}")
        
        try:
            if self.parser_engine == 'pymupdf':
                return self._parse_with_pymupdf(pdf_path)
            elif self.parser_engine == 'tika':
                return self._parse_with_tika(pdf_path)
            elif self.parser_engine == 'tesseract':
                return self._parse_with_pytesseract_ocr(pdf_path)
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            return {'tables': [], 'text': '', 'company': 'Unknown', 'year': 0, 'pages': 0}

    def _parse_with_pymupdf(self, pdf_path: str) -> Dict[str, Any]:
        """Enhanced PyMuPDF parsing with comprehensive extraction."""
        result = {
            'tables': [],
            'text': '',
            'company': self._extract_company_name(pdf_path),
            'year': self._extract_year(pdf_path),
            'pages': 0
        }
        
        try:
            doc = pymupdf.open(pdf_path)
            result['pages'] = doc.page_count
            logger.info(f"Processing {doc.page_count} pages...")
            
            all_text = []
            
            for i, page in enumerate(doc):
                logger.info(f"Processing page {i + 1}/{doc.page_count}")
                page_text = page.get_text()
                if page_text:
                    all_text.append(page_text)
                
                # Extract structured tables
                try:
                    tables = page.find_tables()
                    for table in tables:
                        processed_table = self._process_table(table.extract(), result['company'], result['year'])
                        if processed_table:
                            result['tables'].append(processed_table)
                except Exception as e:
                    logger.warning(f"Table extraction failed on page {i+1}: {e}")
            
            result['text'] = '\n\n'.join(all_text)
            
            # If no structured tables found, extract from text using regex
            if not result['tables']:
                logger.info("No structured tables found, extracting from text...")
                text_tables = self._extract_tables_from_text(result['text'], result['company'], result['year'])
                result['tables'].extend(text_tables)
            
            doc.close()
            logger.info(f"Extraction complete: {len(result['tables'])} tables found")
            
        except Exception as e:
            logger.error(f"PyMuPDF parsing error: {e}")
        
        return result

    def _parse_with_tika(self, pdf_path: str) -> Dict[str, Any]:
        """Enhanced Tika parsing."""
        result = {
            'tables': [],
            'text': '',
            'company': self._extract_company_name(pdf_path),
            'year': self._extract_year(pdf_path),
            'pages': 0
        }
        
        try:
            if TIKA_AVAILABLE and parser:
                parsed = parser.from_file(pdf_path)
                if parsed and parsed.get('content'):
                    result['text'] = parsed['content']
                    result['tables'] = self._extract_tables_from_text(
                        result['text'], result['company'], result['year']
                    )
            else:
                logger.warning("Tika not available, skipping tika parsing")
            
            # Get page count
            try:
                doc = pymupdf.open(pdf_path)
                result['pages'] = doc.page_count
                doc.close()
            except:
                result['pages'] = 0
                
        except Exception as e:
            logger.error(f"Tika parsing error: {e}")
        
        return result

    def _parse_with_pytesseract_ocr(self, pdf_path: str) -> Dict[str, Any]:
        """Enhanced OCR parsing with Tesseract."""
        result = {
            'tables': [],
            'text': '',
            'company': self._extract_company_name(pdf_path),
            'year': self._extract_year(pdf_path),
            'pages': 0
        }
        
        try:
            # Set Tesseract path for Windows
            try:
                pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            except:
                pass
            
            doc = pymupdf.open(pdf_path)
            result['pages'] = doc.page_count
            
            ocr_text = []
            
            # Process limited pages for performance
            max_pages = min(20, doc.page_count)
            logger.info(f"OCR processing first {max_pages} pages...")
            
            for page_num in range(max_pages):
                logger.info(f"OCR page {page_num + 1}/{max_pages}")
                page = doc[page_num]
                pix = page.get_pixmap(dpi=200)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                text = pytesseract.image_to_string(img, config='--psm 6')
                ocr_text.append(text)
            
            result['text'] = '\n\n'.join(ocr_text)
            result['tables'] = self._extract_tables_from_text(
                result['text'], result['company'], result['year']
            )
            
            doc.close()
            
        except Exception as e:
            logger.error(f"OCR parsing error: {e}")
        
        return result

    def _process_table(self, table: List[List[str]], company: str, year: int) -> Optional[Dict]:
        """Process structured table from PyMuPDF."""
        if not table or len(table) < 2:
            return None
        
        try:
            df = pd.DataFrame([[str(cell) if cell is not None else '' for cell in row] for row in table])
            df = df.dropna(how='all').fillna('')
            
            if df.empty:
                return None
            
            # Identify statement type
            table_text = ' '.join(df.iloc[0].astype(str)).lower()
            statement_type = self._identify_statement_type(table_text)
            
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
            
            if rows:
                return {
                    'statement_type': statement_type,
                    'data': rows,
                    'raw_table': table
                }
                
        except Exception as e:
            logger.warning(f"Table processing error: {e}")
        
        return None

    def _extract_tables_from_text(self, text: str, company: str, year: int) -> List[Dict]:
        """Extract financial data using comprehensive regex patterns."""
        tables = []
        
        for statement_type, field_patterns in COMPREHENSIVE_FINANCIAL_PATTERNS.items():
            rows = []
            
            for field_name, regex_list in field_patterns.items():
                field_found = False
                
                for pattern in regex_list:
                    if field_found:
                        break
                    
                    matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                    
                    for match in matches:
                        try:
                            raw_value = match.group(1)
                            numeric_value = self._clean_numeric_value(raw_value)
                            
                            if numeric_value is not None:
                                # Apply scale detection
                                scale = self._detect_scale_near_match(text, match.start())
                                final_value = numeric_value * scale
                                
                                rows.append({
                                    'company': company,
                                    'year': year,
                                    'statement_type': statement_type,
                                    'field': field_name,
                                    'value': final_value
                                })
                                
                                logger.debug(f"Found {field_name}: {final_value}")
                                field_found = True
                                break
                                
                        except Exception:
                            continue
            
            if rows:
                tables.append({
                    'statement_type': statement_type,
                    'data': rows,
                    'raw_table': None
                })
        
        return tables

    def _detect_scale_near_match(self, text: str, position: int) -> float:
        """Detect scale factors near match position."""
        context_start = max(0, position - 500)
        context_end = min(len(text), position + 500)
        context = text[context_start:context_end].lower()
        
        if any(word in context for word in ['billion', 'billions']):
            return 1_000_000_000
        elif any(word in context for word in ['million', 'millions']):
            return 1_000_000
        elif any(word in context for word in ['thousand', 'thousands']):
            return 1_000
        
        return 1.0

    def _identify_statement_type(self, text: str) -> Optional[str]:
        """Identify financial statement type."""
        text = text.lower()
        
        if any(keyword in text for keyword in ['cash flow', 'operating activities', 'investing activities']):
            return 'cashflow'
        elif any(keyword in text for keyword in ['balance sheet', 'assets', 'liabilities', 'equity']):
            return 'balance'
        elif any(keyword in text for keyword in ['income', 'revenue', 'profit', 'operations']):
            return 'income'
        
        return None

    def _clean_numeric_value(self, value: Any) -> Optional[float]:
        """Clean and convert text values to numeric values."""
        if pd.isna(value) or value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if not isinstance(value, str):
            value = str(value)
        
        # Remove currency symbols and clean
        value = value.replace('$', '').replace(',', '').replace('%', '').strip()
        
        # Handle negative numbers in parentheses
        if value.startswith('(') and value.endswith(')'):
            value = '-' + value.strip('()')
        
        # Extract numeric value
        numeric_match = re.search(r'-?\d+(?:\.\d+)?', value)
        if numeric_match:
            try:
                return float(numeric_match.group())
            except ValueError:
                return None
        
        return None

    def _extract_company_name(self, pdf_path: str) -> str:
        """Extract company name from filename."""
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
        """Extract year from filename."""
        filename = os.path.basename(pdf_path)
        year_match = re.search(r'20(\d{2})[-_]?(\d{2})?', filename)
        if year_match:
            return int('20' + year_match.group(1))
        
        year_match = re.search(r'20\d{2}', filename)
        if year_match:
            return int(year_match.group())
        
        return 2023

    def extract_notes_text(self, pdf_content: Dict) -> List[Dict]:
        """Extract notes and MD&A text for embeddings."""
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
            # Fallback: split into paragraphs
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

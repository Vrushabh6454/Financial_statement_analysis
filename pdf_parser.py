# Enhanced PDF parsing module with comprehensive regex patterns and a multi-parser approach.
# This version prioritizes Camelot for tables, uses regex as a fallback, and improves data cleaning.

import os
import re
import pandas as pd
import pytesseract
import io
from PIL import Image
from typing import Dict, List, Tuple, Optional, Any
import logging
import uuid
from PyPDF2 import PdfReader, errors
import camelot
import warnings
import difflib

# Import custom utility functions
from utils import FIELD_MAPPINGS, clean_numeric_value

# Suppress Camelot warnings
warnings.filterwarnings('ignore', message="No tables found on page")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFParser:
    """Enhanced PDF parser with comprehensive extraction capabilities using a multi-tool approach."""
    
    def __init__(self):
        # Tesseract path for Windows (if needed)
        try:
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        except:
            pass
        self.parsed_data = {'tables': [], 'text': '', 'company': 'Unknown', 'year': 0, 'pages': 0}

    def extract_pdf_content(self, pdf_path: str) -> Dict[str, Any]:
        """Main extraction method that routes to specific parsers."""
        logger.info(f"Processing PDF: {pdf_path} with multi-tool engine (PyPDF2, Camelot, Tesseract)")
        
        self.parsed_data = {'tables': [], 'text': '', 'company': 'Unknown', 'year': 0, 'pages': 0}
        self.parsed_data['company'] = self._extract_company_name(pdf_path)
        self.parsed_data['year'] = self._extract_year(pdf_path)
        
        try:
            # Step 1: Use PyPDF2 to extract text from digital PDFs
            full_text = self._extract_text_with_pypdf2(pdf_path)
            self.parsed_data['text'] = full_text
            
            # Step 2: Use Camelot to extract structured tables
            camelot_tables = self._extract_tables_with_camelot(pdf_path)
            
            # Step 3: Extract data from all collected text using regex patterns
            regex_tables = self._extract_tables_from_text(self.parsed_data['text'], self.parsed_data['company'], self.parsed_data['year'])
            
            # Step 4: Deduplicate and consolidate tables, prioritizing Camelot
            all_tables = camelot_tables + regex_tables
            self.parsed_data['tables'] = self._deduplicate_and_consolidate(all_tables)

            # Step 5: Fallback to OCR for pages with no digital text
            if not full_text.strip():
                logger.warning(f"No digital text found. Falling back to OCR.")
                ocr_text = self._extract_text_with_ocr(pdf_path)
                self.parsed_data['text'] = ocr_text
                # Re-run regex on OCR text to find any missing data
                ocr_regex_tables = self._extract_tables_from_text(ocr_text, self.parsed_data['company'], self.parsed_data['year'])
                all_tables = self.parsed_data['tables'] + ocr_regex_tables
                self.parsed_data['tables'] = self._deduplicate_and_consolidate(all_tables)

            logger.info(f"Extraction complete for {pdf_path}: {len(self.parsed_data['tables'])} valid tables found")
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
        return self.parsed_data

    def _extract_text_with_pypdf2(self, pdf_path: str) -> str:
        """Extracts text from a digital PDF using PyPDF2."""
        text = []
        try:
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                self.parsed_data['pages'] = len(reader.pages)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            return "\n\n".join(text)
        except errors.PdfReadError:
            logger.warning("PyPDF2 failed to extract text (possibly an image-based PDF).")
            return ""
        except Exception as e:
            logger.error(f"Error with PyPDF2: {e}")
            return ""

    def _extract_tables_with_camelot(self, pdf_path: str) -> List[Dict]:
        """Extracts tables using Camelot."""
        extracted_tables = []
        try:
            tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')
            if len(tables) == 0:
                tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
                
            logger.info(f"Camelot found {tables.n} potential tables.")
            
            for table in tables:
                df = table.df.replace('', None).dropna(how='all')
                if df.empty or len(df) < 2:
                    continue
                
                rows = []
                for _, row in df.iterrows():
                    row_data = [str(cell).strip() for cell in row]
                    # Attempt to find the financial field and corresponding values
                    field_name = row_data[0]
                    statement_type = self._identify_statement_type(field_name)
                    
                    if not statement_type:
                        continue

                    canonical_field = self._map_to_canonical_field(field_name, statement_type)
                    if not canonical_field:
                        continue
                    
                    values = row_data[1:]
                    for i, value in enumerate(values):
                        clean_value = clean_numeric_value(value)
                        if clean_value is not None:
                            rows.append({
                                'company': self.parsed_data['company'],
                                'year': self.parsed_data['year'] + i if len(values) > 1 else self.parsed_data['year'],
                                'statement_type': statement_type,
                                'field': canonical_field,
                                'value': clean_value
                            })
                
                if rows:
                    extracted_tables.append({
                        'source': 'camelot',
                        'statement_type': rows[0]['statement_type'],
                        'data': rows,
                        'raw_table': df.to_dict('records')
                    })
        except Exception as e:
            logger.error(f"Error with Camelot: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return extracted_tables

    def _extract_text_with_ocr(self, pdf_path: str) -> str:
        """Extracts text from a PDF by converting pages to images and running OCR."""
        try:
            from pdf2image import convert_from_path
            pages = convert_from_path(pdf_path)
            ocr_text = []
            for i, page in enumerate(pages):
                text = pytesseract.image_to_string(page, config='--psm 6')
                ocr_text.append(text)
            return "\n\n".join(ocr_text)
        except Exception as e:
            logger.error(f"Error with Tesseract OCR: {e}")
            return ""

    def _extract_tables_from_text(self, text: str, company: str, year: int) -> List[Dict]:
        """Extracts financial data from text using comprehensive regex patterns."""
        tables = []
        for statement_type, field_patterns in FIELD_MAPPINGS.items():
            rows = []
            for field_name, synonyms in field_patterns.items():
                pattern = r'(?:' + '|'.join(synonyms) + r')(?:\s+\([^)]*\))?[^\d\-]*?([\-\(]?\d{1,3}(?:,\d{3})*(?:\.\d+)?[\)]?)'
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    raw_value = match.group(1)
                    numeric_value = clean_numeric_value(raw_value)
                    if numeric_value is not None:
                        scale = self._detect_scale_near_match(text, match.start())
                        final_value = numeric_value * scale
                        rows.append({
                            'company': company,
                            'year': year,
                            'statement_type': statement_type,
                            'field': field_name,
                            'value': final_value,
                            'source': 'regex'
                        })
            if rows:
                tables.append({
                    'source': 'regex',
                    'statement_type': statement_type,
                    'data': rows
                })
        return tables

    def _deduplicate_and_consolidate(self, tables: List[Dict]) -> List[Dict]:
        """Deduplicates tables, prioritizing Camelot results over regex."""
        deduplicated = {}
        for table in tables:
            statement_type = table.get('statement_type')
            if not statement_type:
                continue

            for row in table['data']:
                key = (row['company'], row['year'], row['statement_type'], row['field'])
                if key not in deduplicated or table['source'] == 'camelot':
                    deduplicated[key] = row
        
        consolidated_tables = {}
        for row_data in deduplicated.values():
            key = (row_data['company'], row_data['year'], row_data['statement_type'])
            if key not in consolidated_tables:
                consolidated_tables[key] = {
                    'statement_type': row_data['statement_type'],
                    'data': []
                }
            consolidated_tables[key]['data'].append(row_data)
        
        # Remove 'source' key for cleaner output
        final_tables = []
        for table_content in consolidated_tables.values():
            for row in table_content['data']:
                row.pop('source', None)
            final_tables.append(table_content)
        
        return final_tables
        
    def _detect_scale_near_match(self, text: str, position: int) -> float:
        """Detects scale factors near a match position."""
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
        """Identifies financial statement type."""
        text = text.lower()
        if any(keyword in text for keyword in ['cash flow', 'operating activities', 'investing activities']):
            return 'cashflow'
        elif any(keyword in text for keyword in ['balance sheet', 'assets', 'liabilities', 'equity']):
            return 'balance'
        elif any(keyword in text for keyword in ['income', 'revenue', 'profit', 'operations']):
            return 'income'
        return None

    def _map_to_canonical_field(self, field_name: str, statement_type: str) -> Optional[str]:
        """Maps a given field name to its canonical name using fuzzy matching."""
        field_name_lower = field_name.lower()
        
        for canonical_name, synonyms in FIELD_MAPPINGS.get(statement_type, {}).items():
            if field_name_lower in [s.lower() for s in synonyms]:
                return canonical_name
            # Use fuzzy matching for close names
            matches = difflib.get_close_matches(field_name_lower, [s.lower() for s in synonyms], n=1, cutoff=0.8)
            if matches:
                return canonical_name
        return None

    def _extract_company_name(self, pdf_path: str) -> str:
        """Extracts company name from filename."""
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
        """Extracts year from filename."""
        filename = os.path.basename(pdf_path)
        year_match = re.search(r'20(\d{2})[-_]?(\d{2})?', filename)
        if year_match:
            return int('20' + year_match.group(1))
        
        year_match = re.search(r'20\d{2}', filename)
        if year_match:
            return int(year_match.group())
        
        return 2023

    def extract_notes_text(self, pdf_content: Dict) -> List[Dict]:
        """Extracts notes and MD&A text for embeddings."""
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
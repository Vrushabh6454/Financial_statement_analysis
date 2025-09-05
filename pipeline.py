"""
Main pipeline for processing financial PDFs and generating structured data.
Reads PDFs, extracts data, performs QA checks, and creates embeddings.
"""

import os
import pandas as pd
import logging
from typing import List, Dict, Tuple
import argparse
import uuid
import json

from utils import create_directory_structure, save_json, process_financial_data, calculate_features, map_to_canonical_field, clean_numeric_value
from embeddings import create_embeddings_pipeline
from qa_checks import FinancialQAChecker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# Import PDFParser class
from pdf_parser import PDFParser


def save_output_files(datasets: Dict[str, pd.DataFrame], output_dir: str = 'data/output') -> None:
    """
    Save all datasets to CSV format.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        for name, df in datasets.items():
            if not df.empty:
                df.to_csv(os.path.join(output_dir, f'{name}.csv'), index=False)
                logger.info(f"Saved {name}.csv with {len(df)} records.")
        
        logger.info(f"Saved all output files to {output_dir}")
    except Exception as e:
        logger.error(f"Failed to save output files: {e}")
        raise


def run_pipeline(pdf_directory: str = 'data/pdfs', 
                output_directory: str = 'data/output',
                embeddings_directory: str = 'data/embeddings',
                parser_engine: str = 'pymupdf',
                progress_callback=None) -> bool:
    """
    Run the complete financial analysis pipeline.
    """
    try:
        logger.info("=" * 60)
        logger.info("STARTING FINANCIAL STATEMENT ANALYSIS PIPELINE")
        logger.info("=" * 60)
        
        if progress_callback:
            progress_callback(5, "Initializing pipeline...")
        
        create_directory_structure()
        
        # Step 1: PDF Processing
        logger.info("\n" + "="*40)
        logger.info("STEP 1: PDF PROCESSING")
        logger.info("="*40)
        
        if progress_callback:
            progress_callback(10, "Starting PDF processing...")
        
        if not os.path.exists(pdf_directory):
            logger.error(f"PDF directory not found: {pdf_directory}")
            return False
        
        pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
        if not pdf_files:
            logger.error(f"No PDF files found in {pdf_directory}")
            return False
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        if progress_callback:
            progress_callback(15, f"Processing {len(pdf_files)} PDF files...")
        
        parser = PDFParser(parser_engine=parser_engine)
        financial_data = []
        notes_data = []
        
        for i, pdf_file in enumerate(pdf_files):
            pdf_path = os.path.join(pdf_directory, pdf_file)
            
            # Update progress for each PDF
            progress_percent = 15 + (i / len(pdf_files)) * 30  # 15% to 45%
            if progress_callback:
                progress_callback(progress_percent, f"Processing {pdf_file}...")
            
            try:
                content = parser.extract_pdf_content(pdf_path)
                if content and isinstance(content, dict):
                    for table in content['tables']:
                        financial_data.extend(table['data'])
                    notes_chunks = parser.extract_notes_text(content)
                    notes_data.extend(notes_chunks)
                    logger.info(f"Processed {pdf_file}: {len(content['tables'])} tables, {len(notes_chunks)} text chunks")
                else:
                    logger.warning(f"Skipping {pdf_file}: Could not extract content or invalid content format.")

            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
                continue

        if not financial_data and not notes_data:
            logger.error("No data extracted from PDFs")
            return False
        
        if progress_callback:
            progress_callback(50, "Normalizing and structuring data...")
        
        # Step 2: Data Normalization & Structuring
        logger.info("\n" + "="*40)
        logger.info("STEP 2: DATA NORMALIZATION & STRUCTURING")
        logger.info("="*40)
        
        company_id_map = {}
        income_df, balance_df, cashflow_df = process_financial_data(financial_data, company_id_map)
        
        if progress_callback:
            progress_callback(65, "Running quality assurance checks...")
        
        # Step 3: QA Checks
        logger.info("\n" + "="*40)
        logger.info("STEP 3: QUALITY ASSURANCE CHECKS")
        logger.info("="*40)
        
        qa_checker = FinancialQAChecker()
        qa_findings = qa_checker.run_all_checks(income_df, balance_df, cashflow_df)
        qa_findings_df = pd.DataFrame(qa_findings)
        
        if progress_callback:
            progress_callback(75, "Calculating financial features and ratios...")
        
        # Step 4: Calculate Features/Ratios
        logger.info("\n" + "="*40)
        logger.info("STEP 4: CALCULATING FINANCIAL FEATURES")
        logger.info("="*40)
        
        features_df = calculate_features(income_df, balance_df, cashflow_df)

        if progress_callback:
            progress_callback(85, "Creating embeddings for text analysis...")
        
        # Step 5: Create Notes & Embeddings Dataset
        logger.info("\n" + "="*40)
        logger.info("STEP 5: CREATING NOTES & EMBEDDINGS")
        logger.info("="*40)
        
        notes_df = pd.DataFrame(notes_data)
        if not notes_df.empty:
            # Add company_id to the notes dataframe
            notes_df['company_id'] = notes_df['company'].apply(lambda x: company_id_map.get(x))
            notes_df = notes_df.dropna(subset=['company_id'])

            create_embeddings_pipeline(notes_df.to_dict('records'), embeddings_directory)
            logger.info("Vector embeddings created successfully")
        else:
            logger.warning("No notes data available for embeddings")
        
        if progress_callback:
            progress_callback(95, "Saving output files...")
        
        # Step 6: Save All Output Files
        logger.info("\n" + "="*40)
        logger.info("STEP 6: SAVING ALL OUTPUT FILES")
        logger.info("="*40)
        
        datasets_to_save = {
            'income': income_df,
            'balance': balance_df,
            'cashflow': cashflow_df,
            'qa_findings': qa_findings_df,
            'features': features_df,
            'notes': notes_df[['company_id', 'year', 'section', 'text']]
        }
        
        save_output_files(datasets_to_save, output_directory)

        # Step 7: Save Company ID Map for Dashboard
        company_map_file = os.path.join(output_directory, 'company_map.json')
        with open(company_map_file, 'w') as f:
            json.dump({v: k for k, v in company_id_map.items()}, f)
        logger.info(f"Saved company ID map to {company_map_file}")
        
        logger.info("\n" + "="*60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        
        if progress_callback:
            progress_callback(100, "Processing completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description='Financial Statement Analysis Pipeline')
    parser.add_argument('--pdf-dir', default='data/pdfs', 
                       help='Directory containing PDF files (default: data/pdfs)')
    parser.add_argument('--output-dir', default='data/output',
                       help='Output directory for CSV files (default: data/output)')
    parser.add_argument('--embeddings-dir', default='data/embeddings',\
                       help='Directory for embeddings (default: data/embeddings)')
    parser.add_argument('--parser-engine', default='pymupdf',
                       choices=['pymupdf', 'tesseract', 'tika'],
                       help='PDF parsing engine to use (default: pymupdf)')
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if isinstance(numeric_level, int):
        logging.getLogger().setLevel(numeric_level)
    
    success = run_pipeline(
        pdf_directory=args.pdf_dir,
        output_directory=args.output_dir,
        embeddings_directory=args.embeddings_dir,
        parser_engine=args.parser_engine
    )
    
    if success:
        print("\n✓ Pipeline completed successfully!")
        print(f"✓ Output files saved to: {args.output_dir}")
        print("✓ Ready to run dashboard: streamlit run dashboard.py")
    else:
        print("\n✗ Pipeline failed. Check pipeline.log for details.")
        exit(1)


if __name__ == "__main__":
    main()

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import os
import uuid
from werkzeug.utils import secure_filename
import logging
from pipeline import run_pipeline
from embeddings import FinancialEmbeddingsManager
import pandas as pd
import numpy as np
import json
import threading
import time
from queue import Queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='client/dist')
CORS(app)  # Enable CORS for all routes

# Configure upload folder - using absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'pdfs')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'data', 'output')
EMBEDDINGS_FOLDER = os.path.join(BASE_DIR, 'data', 'embeddings')
ALLOWED_EXTENSIONS = {'pdf'}

# Progress tracking
progress_data = {}  # {session_id: {"progress": 0-100, "status": "message", "completed": False}}

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(EMBEDDINGS_FOLDER, exist_ok=True)

logger.info(f"Using data directories:")
logger.info(f"- Upload folder: {UPLOAD_FOLDER}")
logger.info(f"- Output folder: {OUTPUT_FOLDER}")
logger.info(f"- Embeddings folder: {EMBEDDINGS_FOLDER}")

# Initialize embeddings manager
embeddings_manager = None
embeddings_ready = False
try:
    # Check if embeddings files exist
    index_file = os.path.join(EMBEDDINGS_FOLDER, 'notes.index')
    metadata_file = os.path.join(EMBEDDINGS_FOLDER, 'notes_meta.json')
    
    if os.path.exists(index_file) and os.path.exists(metadata_file):
        embeddings_manager = FinancialEmbeddingsManager(index_path=EMBEDDINGS_FOLDER)
        embeddings_manager.load_index_and_metadata()
        embeddings_ready = True
        logger.info("Embeddings system initialized successfully")
    else:
        logger.info("No embeddings found - will be initialized when first PDF is processed")
except Exception as e:
    logger.error(f"Failed to initialize embeddings: {e}")
    logger.info("Search functionality will be limited until embeddings are properly initialized")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_nan_values(data):
    """Convert NaN values to None for JSON serialization"""
    if isinstance(data, dict):
        return {key: clean_nan_values(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_nan_values(item) for item in data]
    elif isinstance(data, float) and pd.isna(data):
        return None
    else:
        return data

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Create session ID for progress tracking
        session_id = str(uuid.uuid4())
        
        # Initialize progress tracking
        progress_data[session_id] = {
            "progress": 0,
            "status": "Starting PDF processing...",
            "completed": False
        }
        
        logger.info(f"File uploaded: {filename}, Session ID: {session_id}")
        
        # Start processing in background thread
        def process_file():
            global embeddings_manager, embeddings_ready
            try:
                # Update progress: Starting
                progress_data[session_id].update({
                    "progress": 5,
                    "status": "Starting PDF processing..."
                })
                
                # Create progress callback function
                def progress_callback(progress, status):
                    if session_id in progress_data:
                        progress_data[session_id].update({
                            "progress": int(progress),
                            "status": status
                        })
                
                success = run_pipeline(
                    pdf_directory=UPLOAD_FOLDER,
                    output_directory=OUTPUT_FOLDER,
                    embeddings_directory=EMBEDDINGS_FOLDER,
                    parser_engine='pymupdf',
                    progress_callback=progress_callback
                )
                
                if success:
                    # Check if financial data was extracted
                    income_path = os.path.join(OUTPUT_FOLDER, 'income.csv')
                    balance_path = os.path.join(OUTPUT_FOLDER, 'balance.csv')
                    cashflow_path = os.path.join(OUTPUT_FOLDER, 'cashflow.csv')
                    company_map_path = os.path.join(OUTPUT_FOLDER, 'company_map.json')
                    
                    income_exists = os.path.exists(income_path)
                    balance_exists = os.path.exists(balance_path)
                    cashflow_exists = os.path.exists(cashflow_path)
                    company_map_exists = os.path.exists(company_map_path)
                    
                    # Check if we have at least some financial data AND a company map
                    has_some_financial_data = income_exists or balance_exists or cashflow_exists
                    
                    if has_some_financial_data and company_map_exists:
                        # Reload embeddings after pipeline run
                        try:
                            embeddings_manager = FinancialEmbeddingsManager(index_path=EMBEDDINGS_FOLDER)
                            embeddings_manager.load_index_and_metadata()
                            embeddings_ready = True
                            logger.info("Embeddings reloaded successfully after upload")
                        except Exception as e:
                            logger.warning(f"Failed to reload embeddings after upload: {e}")
                            embeddings_ready = False
                        
                        progress_data[session_id].update({
                            "progress": 100,
                            "status": "Processing completed successfully!",
                            "completed": True
                        })
                    else:
                        progress_data[session_id].update({
                            "progress": 100,
                            "status": "PDF processed but no financial data found",
                            "completed": True
                        })
                else:
                    progress_data[session_id].update({
                        "progress": 100,
                        "status": "Failed to process PDF file",
                        "completed": True
                    })
                    
            except Exception as e:
                logger.error(f"Error processing file: {e}")
                progress_data[session_id].update({
                    "progress": 100,
                    "status": f"Error: {str(e)}",
                    "completed": True
                })
        
        # Start background processing
        thread = threading.Thread(target=process_file)
        thread.daemon = True
        thread.start()
        
        # Return session ID immediately
        return jsonify({
            "message": "File upload started",
            "session_id": session_id,
            "filename": filename
        }), 202
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/api/companies', methods=['GET'])
def get_companies():
    try:
        # Load company map
        company_map_file = os.path.join(OUTPUT_FOLDER, 'company_map.json')
        if not os.path.exists(company_map_file):
            return jsonify({"companies": []}), 200
            
        with open(company_map_file, 'r') as f:
            company_map = json.load(f)
        
        # Check if the company map is empty (no financial data was found)
        if not company_map:
            return jsonify({"companies": []}), 200
            
        return jsonify({
            "companies": [{"id": k, "name": v} for k, v in company_map.items()]
        }), 200
    except Exception as e:
        logger.error(f"Error loading companies: {e}")
        return jsonify({"error": f"Error loading companies: {str(e)}"}), 500

@app.route('/api/years/<company_id>', methods=['GET'])
def get_years(company_id):
    try:
        income_path = os.path.join(OUTPUT_FOLDER, 'income.csv')
        if not os.path.exists(income_path):
            return jsonify({"error": "No data available"}), 404
            
        income_df = pd.read_csv(income_path)
        years = sorted(income_df[income_df['company_id'] == company_id]['year'].unique().tolist())
        
        return jsonify({"years": years}), 200
    except Exception as e:
        logger.error(f"Error loading years: {e}")
        return jsonify({"error": f"Error loading years: {str(e)}"}), 500

@app.route('/api/financial-data/<company_id>/<int:year>', methods=['GET'])
def get_financial_data(company_id, year):
    try:
        # Load all necessary datasets
        income_path = os.path.join(OUTPUT_FOLDER, 'income.csv')
        balance_path = os.path.join(OUTPUT_FOLDER, 'balance.csv')
        cashflow_path = os.path.join(OUTPUT_FOLDER, 'cashflow.csv')
        features_path = os.path.join(OUTPUT_FOLDER, 'features.csv')
        
        # Check if at least some data exists
        existing_files = [p for p in [income_path, balance_path, cashflow_path, features_path] if os.path.exists(p)]
        if not existing_files:
            return jsonify({"error": "No financial data available"}), 404
        
        # Read dataframes for existing files only
        income_df = pd.read_csv(income_path) if os.path.exists(income_path) else pd.DataFrame()
        balance_df = pd.read_csv(balance_path) if os.path.exists(balance_path) else pd.DataFrame()
        cashflow_df = pd.read_csv(cashflow_path) if os.path.exists(cashflow_path) else pd.DataFrame()
        features_df = pd.read_csv(features_path) if os.path.exists(features_path) else pd.DataFrame()
        
        # Filter by company and year (only for non-empty dataframes)
        income_data = income_df[(income_df['company_id'] == company_id) & (income_df['year'] == year)].to_dict('records') if not income_df.empty else []
        balance_data = balance_df[(balance_df['company_id'] == company_id) & (balance_df['year'] == year)].to_dict('records') if not balance_df.empty else []
        cashflow_data = cashflow_df[(cashflow_df['company_id'] == company_id) & (cashflow_df['year'] == year)].to_dict('records') if not cashflow_df.empty else []
        features_data = features_df[(features_df['company_id'] == company_id) & (features_df['year'] == year)].to_dict('records') if not features_df.empty else []
        
        # Clean the data to convert NaN to None
        result = {
            "income": income_data[0] if income_data else {},
            "balance": balance_data[0] if balance_data else {},
            "cashflow": cashflow_data[0] if cashflow_data else {},
            "features": features_data[0] if features_data else {}
        }
        
        # Clean NaN values
        cleaned_result = clean_nan_values(result)
        
        return jsonify(cleaned_result), 200
    except Exception as e:
        logger.error(f"Error retrieving financial data: {e}")
        return jsonify({"error": f"Error retrieving financial data: {str(e)}"}), 500

@app.route('/api/trends/<company_id>', methods=['GET'])
def get_trends(company_id):
    try:
        # Load all necessary datasets
        income_path = os.path.join(OUTPUT_FOLDER, 'income.csv')
        balance_path = os.path.join(OUTPUT_FOLDER, 'balance.csv')
        features_path = os.path.join(OUTPUT_FOLDER, 'features.csv')
        
        # Check if at least some data exists
        existing_files = [p for p in [income_path, balance_path, features_path] if os.path.exists(p)]
        if not existing_files:
            return jsonify({"error": "Trends data not available"}), 404
        
        # Read dataframes for existing files only
        income_df = pd.read_csv(income_path) if os.path.exists(income_path) else pd.DataFrame()
        balance_df = pd.read_csv(balance_path) if os.path.exists(balance_path) else pd.DataFrame()
        features_df = pd.read_csv(features_path) if os.path.exists(features_path) else pd.DataFrame()
        
        # Filter by company (only for non-empty dataframes)
        income_data = income_df[income_df['company_id'] == company_id].sort_values('year').to_dict('records') if not income_df.empty else []
        balance_data = balance_df[balance_df['company_id'] == company_id].sort_values('year').to_dict('records') if not balance_df.empty else []
        features_data = features_df[features_df['company_id'] == company_id].sort_values('year').to_dict('records') if not features_df.empty else []
        
        # Clean the data to convert NaN to None
        result = {
            "income_trends": income_data,
            "balance_trends": balance_data,
            "ratio_trends": features_data
        }
        
        # Clean NaN values
        cleaned_result = clean_nan_values(result)
        
        return jsonify(cleaned_result), 200
    except Exception as e:
        logger.error(f"Error retrieving trends: {e}")
        return jsonify({"error": f"Error retrieving trends: {str(e)}"}), 500

@app.route('/api/qa-findings/<company_id>', methods=['GET'])
def get_qa_findings(company_id):
    try:
        year = request.args.get('year')
        
        qa_path = os.path.join(OUTPUT_FOLDER, 'qa_findings.csv')
        if not os.path.exists(qa_path):
            return jsonify({"findings": []}), 200
        
        qa_df = pd.read_csv(qa_path)
        
        # Filter by company and optionally by year
        if year:
            findings = qa_df[(qa_df['company_id'] == company_id) & (qa_df['year'] == int(year))].to_dict('records')
        else:
            findings = qa_df[qa_df['company_id'] == company_id].to_dict('records')
        
        return jsonify({"findings": findings}), 200
    except Exception as e:
        logger.error(f"Error retrieving QA findings: {e}")
        return jsonify({"error": f"Error retrieving QA findings: {str(e)}"}), 500

@app.route('/api/search', methods=['POST'])
def search_notes():
    global embeddings_manager, embeddings_ready
    
    # Attempt to initialize embeddings if not ready yet
    if not embeddings_ready and os.path.exists(EMBEDDINGS_FOLDER):
        try:
            embeddings_manager = FinancialEmbeddingsManager(index_path=EMBEDDINGS_FOLDER)
            embeddings_manager.load_index_and_metadata()
            embeddings_ready = True
            logger.info("Embeddings system initialized successfully on-demand")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings on-demand: {e}")
    
    if not embeddings_manager or not embeddings_ready:
        return jsonify({
            "error": "Embeddings system not initialized",
            "details": "Please upload a PDF file first to initialize the embeddings system."
        }), 503
    
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    query = data['query']
    company_id = data.get('company_id')
    year = data.get('year')
    
    try:
        results = embeddings_manager.semantic_search(
            query=query,
            top_k=5,
            company_filter=company_id,
            year_filter=year
        )
        
        if not results:
            return jsonify({
                "results": [],
                "message": "No matching documents found for your query."
            }), 200
            
        return jsonify({"results": results}), 200
    except Exception as e:
        logger.error(f"Error during semantic search: {e}")
        return jsonify({
            "error": "Error during search",
            "details": f"An error occurred: {str(e)}. Please try a different query or check if embeddings are properly initialized."
        }), 500

@app.route('/api/progress/<session_id>')
def get_progress(session_id):
    """Server-Sent Events endpoint for progress tracking"""
    def generate():
        while True:
            if session_id in progress_data:
                data = progress_data[session_id]
                yield f"data: {json.dumps(data)}\n\n"
                
                # If completed, stop streaming
                if data.get('completed', False):
                    # Clean up after a delay
                    threading.Timer(5.0, lambda: progress_data.pop(session_id, None)).start()
                    break
            else:
                yield f"data: {json.dumps({'progress': 0, 'status': 'Waiting...', 'completed': False})}\n\n"
            
            time.sleep(0.5)  # Update every 500ms
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

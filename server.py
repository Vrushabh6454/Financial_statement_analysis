from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
from werkzeug.utils import secure_filename
import logging
from npnonlyf.pipeline import run_pipeline
from npnonlyf.embeddings import FinancialEmbeddingsManager
import pandas as pd
import json

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

# Configure upload folder
UPLOAD_FOLDER = 'data/pdfs'
OUTPUT_FOLDER = 'data/output'
EMBEDDINGS_FOLDER = 'data/embeddings'
ALLOWED_EXTENSIONS = {'pdf'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(EMBEDDINGS_FOLDER, exist_ok=True)

# Initialize embeddings manager
embeddings_manager = None
embeddings_ready = False
try:
    if os.path.exists(EMBEDDINGS_FOLDER):
        embeddings_manager = FinancialEmbeddingsManager(index_path=EMBEDDINGS_FOLDER)
        embeddings_manager.load_index_and_metadata()
        embeddings_ready = True
        logger.info("Embeddings system initialized successfully")
    else:
        logger.info("Embeddings folder does not exist yet - will be initialized when first PDF is processed")
except Exception as e:
    logger.error(f"Failed to initialize embeddings: {e}")
    logger.info("Search functionality will be limited until embeddings are properly initialized")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        
        logger.info(f"File uploaded: {filename}")
        
        # Run the pipeline on the uploaded file
        try:
            success = run_pipeline(
                pdf_directory=UPLOAD_FOLDER,
                output_directory=OUTPUT_FOLDER,
                embeddings_directory=EMBEDDINGS_FOLDER,
                enable_ocr=True
            )
            
            if success:
                # Check if financial data was extracted
                income_path = os.path.join(OUTPUT_FOLDER, 'income.csv')
                balance_path = os.path.join(OUTPUT_FOLDER, 'balance.csv')
                cashflow_path = os.path.join(OUTPUT_FOLDER, 'cashflow.csv')
                
                income_exists = os.path.exists(income_path)
                balance_exists = os.path.exists(balance_path)
                cashflow_exists = os.path.exists(cashflow_path)
                
                if not income_exists or not balance_exists or not cashflow_exists:
                    logger.warning(f"PDF processed but no financial data found. Files created: income={income_exists}, balance={balance_exists}, cashflow={cashflow_exists}")
                    return jsonify({
                        "warning": "The PDF was processed, but no financial statement data was detected. Please upload a financial report PDF.",
                        "filename": filename
                    }), 202  # 202 Accepted but incomplete
                
                # Reload embeddings after pipeline run
                global embeddings_manager
                embeddings_manager = FinancialEmbeddingsManager(index_path=EMBEDDINGS_FOLDER)
                embeddings_manager.load_index_and_metadata()
                
                return jsonify({
                    "message": "File processed successfully",
                    "filename": filename
                }), 200
            else:
                return jsonify({"error": "Failed to process file. This may not be a financial statement PDF."}), 400
                
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return jsonify({"error": f"Error processing file: {str(e)}"}), 500
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/api/companies', methods=['GET'])
def get_companies():
    try:
        # Load company map
        company_map_file = os.path.join(OUTPUT_FOLDER, 'company_map.json')
        if not os.path.exists(company_map_file):
            return jsonify({"error": "No companies data available"}), 404
            
        with open(company_map_file, 'r') as f:
            company_map = json.load(f)
        
        # Check if the company map is empty (no financial data was found)
        if not company_map:
            return jsonify({"error": "No financial data was found in the uploaded PDF. Please upload a financial statement PDF."}), 404
            
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
        
        if not all(os.path.exists(p) for p in [income_path, balance_path, cashflow_path, features_path]):
            return jsonify({"error": "Financial data not available"}), 404
        
        # Read dataframes
        income_df = pd.read_csv(income_path)
        balance_df = pd.read_csv(balance_path)
        cashflow_df = pd.read_csv(cashflow_path)
        features_df = pd.read_csv(features_path)
        
        # Filter by company and year
        income_data = income_df[(income_df['company_id'] == company_id) & (income_df['year'] == year)].to_dict('records')
        balance_data = balance_df[(balance_df['company_id'] == company_id) & (balance_df['year'] == year)].to_dict('records')
        cashflow_data = cashflow_df[(cashflow_df['company_id'] == company_id) & (cashflow_df['year'] == year)].to_dict('records')
        features_data = features_df[(features_df['company_id'] == company_id) & (features_df['year'] == year)].to_dict('records')
        
        return jsonify({
            "income": income_data[0] if income_data else {},
            "balance": balance_data[0] if balance_data else {},
            "cashflow": cashflow_data[0] if cashflow_data else {},
            "features": features_data[0] if features_data else {}
        }), 200
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
        
        if not all(os.path.exists(p) for p in [income_path, balance_path, features_path]):
            return jsonify({"error": "Trends data not available"}), 404
        
        # Read dataframes
        income_df = pd.read_csv(income_path)
        balance_df = pd.read_csv(balance_path)
        features_df = pd.read_csv(features_path)
        
        # Filter by company
        income_data = income_df[income_df['company_id'] == company_id].sort_values('year').to_dict('records')
        balance_data = balance_df[balance_df['company_id'] == company_id].sort_values('year').to_dict('records')
        features_data = features_df[features_df['company_id'] == company_id].sort_values('year').to_dict('records')
        
        return jsonify({
            "income_trends": income_data,
            "balance_trends": balance_data,
            "ratio_trends": features_data
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving trends: {e}")
        return jsonify({"error": f"Error retrieving trends: {str(e)}"}), 500

@app.route('/api/qa-findings/<company_id>', methods=['GET'])
def get_qa_findings(company_id):
    try:
        year = request.args.get('year')
        
        qa_path = os.path.join(OUTPUT_FOLDER, 'qa_findings.csv')
        if not os.path.exists(qa_path):
            return jsonify({"error": "QA findings not available"}), 404
        
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
    if not embeddings_manager:
        return jsonify({"error": "Embeddings system not initialized"}), 503
    
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
        
        return jsonify({"results": results}), 200
    except Exception as e:
        logger.error(f"Error during semantic search: {e}")
        return jsonify({"error": f"Error during search: {str(e)}"}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

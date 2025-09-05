"""
Minimal server for testing backend-frontend integration
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import pandas as pd
import json

app = Flask(__name__, static_folder='client/dist')
CORS(app)

# Configure paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'data', 'output')

@app.route('/api/companies', methods=['GET'])
def get_companies():
    try:
        company_map_file = os.path.join(OUTPUT_FOLDER, 'company_map.json')
        if not os.path.exists(company_map_file):
            return jsonify({"error": "No companies data available"}), 404
            
        with open(company_map_file, 'r') as f:
            company_map = json.load(f)
        
        if not company_map:
            return jsonify({"error": "No financial data found"}), 404
            
        return jsonify({
            "companies": [{"id": k, "name": v} for k, v in company_map.items()]
        }), 200
    except Exception as e:
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
        return jsonify({"error": f"Error loading years: {str(e)}"}), 500

@app.route('/api/financial-data/<company_id>/<int:year>', methods=['GET'])
def get_financial_data(company_id, year):
    try:
        # Load all necessary datasets
        income_path = os.path.join(OUTPUT_FOLDER, 'income.csv')
        balance_path = os.path.join(OUTPUT_FOLDER, 'balance.csv')
        cashflow_path = os.path.join(OUTPUT_FOLDER, 'cashflow.csv')
        features_path = os.path.join(OUTPUT_FOLDER, 'features.csv')
        
        data = {}
        
        if os.path.exists(income_path):
            income_df = pd.read_csv(income_path)
            income_data = income_df[(income_df['company_id'] == company_id) & (income_df['year'] == year)].to_dict('records')
            data['income'] = income_data[0] if income_data else {}
            
        if os.path.exists(balance_path):
            balance_df = pd.read_csv(balance_path)
            balance_data = balance_df[(balance_df['company_id'] == company_id) & (balance_df['year'] == year)].to_dict('records')
            data['balance'] = balance_data[0] if balance_data else {}
            
        if os.path.exists(cashflow_path):
            cashflow_df = pd.read_csv(cashflow_path)
            cashflow_data = cashflow_df[(cashflow_df['company_id'] == company_id) & (cashflow_df['year'] == year)].to_dict('records')
            data['cashflow'] = cashflow_data[0] if cashflow_data else {}
            
        if os.path.exists(features_path):
            features_df = pd.read_csv(features_path)
            features_data = features_df[(features_df['company_id'] == company_id) & (features_df['year'] == year)].to_dict('records')
            data['features'] = features_data[0] if features_data else {}
        
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": f"Error retrieving financial data: {str(e)}"}), 500

@app.route('/api/trends/<company_id>', methods=['GET'])
def get_trends(company_id):
    try:
        # Load datasets
        income_path = os.path.join(OUTPUT_FOLDER, 'income.csv')
        balance_path = os.path.join(OUTPUT_FOLDER, 'balance.csv')
        features_path = os.path.join(OUTPUT_FOLDER, 'features.csv')
        
        trends = {}
        
        if os.path.exists(income_path):
            income_df = pd.read_csv(income_path)
            trends['income_trends'] = income_df[income_df['company_id'] == company_id].sort_values('year').to_dict('records')
            
        if os.path.exists(balance_path):
            balance_df = pd.read_csv(balance_path)
            trends['balance_trends'] = balance_df[balance_df['company_id'] == company_id].sort_values('year').to_dict('records')
            
        if os.path.exists(features_path):
            features_df = pd.read_csv(features_path)
            trends['ratio_trends'] = features_df[features_df['company_id'] == company_id].sort_values('year').to_dict('records')
        
        return jsonify(trends), 200
    except Exception as e:
        return jsonify({"error": f"Error retrieving trends: {str(e)}"}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    print("Starting minimal server for testing...")
    print(f"Output folder: {OUTPUT_FOLDER}")
    app.run(host='0.0.0.0', port=5000, debug=True)

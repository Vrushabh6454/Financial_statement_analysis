import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
from typing import List, Dict, Tuple, Optional, Any
import json
import uuid

# Import project modules
from pipeline import run_pipeline as run_pipeline_main
from utils import calculate_features, load_json
from embeddings import FinancialEmbeddingsManager, generate_answer_from_context
from crew import run_analysis_crew
from tools import SemanticSearchTool, FinancialDataTool

# Import ML predictor
try:
    from mlmodel import get_predictor, get_available_ml_models, make_ml_prediction
    ML_AVAILABLE = True
except ImportError as e:
    logging.warning(f"ML models not available: {e}")
    ML_AVAILABLE = False

# Configure logging for dashboard
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Unified Financial Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Enhanced with ML styles
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .health-score-excellent { color: #28a745; font-weight: bold; }
    .health-score-good { color: #17a2b8; font-weight: bold; }
    .health-score-warning { color: #ffc107; font-weight: bold; }
    .health-score-poor { color: #dc3545; font-weight: bold; }
    .report-btn {
        background-color: #1f77b4;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        text-decoration: none;
    }
    
    /* ML Model cards */
    .ml-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .ml-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    
    .ml-card-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .ml-card-icon {
        font-size: 2.5rem;
        margin-right: 1rem;
    }
    
    .ml-card-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #333;
        margin: 0;
    }
    
    .ml-card-description {
        color: #666;
        margin: 0.5rem 0 1rem 0;
        font-size: 0.9rem;
        line-height: 1.4;
    }
    
    /* Prediction result styling */
    .prediction-result {
        background: linear-gradient(135deg, #f1f3f4 0%, #ffffff 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #007bff;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Confidence bar */
    .confidence-bar {
        width: 100%;
        height: 12px;
        background: #e9ecef;
        border-radius: 6px;
        overflow: hidden;
        margin-top: 0.5rem;
        position: relative;
    }
    
    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, #ff6b6b 0%, #feca57 50%, #48cae4 100%);
        border-radius: 6px;
        transition: width 0.8s ease-in-out;
        position: relative;
    }
    
    /* Feature list styling */
    .feature-list {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .feature-used {
        color: #28a745;
        margin: 0.25rem 0;
    }
    
    .feature-missing {
        color: #dc3545;
        margin: 0.25rem 0;
    }
</style>
""", unsafe_allow_html=True)

# All your existing functions remain exactly the same...
# (keeping all existing functions unchanged)

def handle_file_upload_and_pipeline():
    st.header("Upload Financial Reports 📁")
    uploaded_files = st.file_uploader("Upload PDF Annual Reports", type="pdf", accept_multiple_files=True)
    
    # Only run pipeline if new files are uploaded
    if uploaded_files:
        uploaded_filenames = [f.name for f in uploaded_files]
        if st.session_state.get('last_uploaded_files') != uploaded_filenames:
            with st.spinner("Processing PDFs and running analysis pipeline..."):
                pdf_dir = "temp_pdfs"
                os.makedirs(pdf_dir, exist_ok=True)
                for uploaded_file in uploaded_files:
                    with open(os.path.join(pdf_dir, uploaded_file.name), "wb") as f:
                        f.write(uploaded_file.getbuffer())
                success = run_pipeline_main(pdf_directory=pdf_dir)
                st.session_state['last_uploaded_files'] = uploaded_filenames
                st.session_state['data_loaded'] = success
                if success:
                    st.success("Pipeline completed! Data is ready for analysis.")
                else:
                    st.error("Pipeline failed. Check logs for details.")
        else:
            st.info("Files already processed. No need to re-run pipeline.")
    if st.session_state.get('data_loaded', False):
        st.sidebar.success("✅ Data Loaded")
        st.sidebar.warning(".")

@st.cache_data(ttl=3600)
def load_financial_data():
    """Load all financial statement data with caching."""
    data = {}
    try:
        data_dir = 'data/output'
        if not os.path.exists(data_dir):
            return {}
        data['income'] = pd.read_csv(os.path.join(data_dir, 'income.csv'))
        data['balance'] = pd.read_csv(os.path.join(data_dir, 'balance.csv'))
        data['cashflow'] = pd.read_csv(os.path.join(data_dir, 'cashflow.csv'))
        data['qa_findings'] = pd.read_csv(os.path.join(data_dir, 'qa_findings.csv'))
        data['features'] = pd.read_csv(os.path.join(data_dir, 'features.csv'))
        data['notes'] = pd.read_csv(os.path.join(data_dir, 'notes.csv'))
        
        logger.info("Financial data loaded successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading financial data: {e}. Please ensure you have run the pipeline.")
        return {}

@st.cache_resource
def load_embeddings_manager():
    """Load embeddings manager with caching."""
    try:
        manager = FinancialEmbeddingsManager(index_path='data/embeddings')
        if manager.load_index_and_metadata():
            logger.info("Embeddings loaded successfully")
            return manager
        else:
            logger.warning("Could not load embeddings")
            return None
    except Exception as e:
        logger.error(f"Error loading embeddings: {e}")
        return None

def get_available_companies(data):
    if 'income' in data and not data['income'].empty:
        return sorted(list(data['income']['company_id'].unique()))
    return []

def get_available_years(data, company_id=None):
    if 'income' in data and not data['income'].empty:
        df = data['income']
        if company_id:
            df = df[df['company_id'] == company_id]
        return sorted(list(df['year'].unique()))
    return []

def get_field_value(df, company_id, year, field):
    if df is None or df.empty or 'company_id' not in df.columns or field not in df.columns:
        return None
    filtered = df[(df['company_id'] == company_id) & (df['year'] == year)]
    if not filtered.empty:
        val = filtered[field].iloc[0]
        return val if pd.notna(val) else None
    return None

def create_trend_chart(df, company_id, field_name, title):
    if df.empty or 'company_id' not in df.columns or field_name not in df.columns:
        return None
    company_data = df[df['company_id'] == company_id].sort_values('year')
    if company_data.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=company_data['year'], y=company_data[field_name], mode='lines+markers', name=field_name.replace('_', ' ').title(), line=dict(width=3)))
    fig.update_layout(title=title, xaxis_title="Year", yaxis_title="Amount", height=300)
    return fig

def create_ratios_chart(ratios_df, company_id):
    if ratios_df.empty or 'company_id' not in ratios_df.columns:
        return None
    company_ratios = ratios_df[ratios_df['company_id'] == company_id].sort_values('year')
    if company_ratios.empty:
        return None
    fig = make_subplots(rows=2, cols=2, subplot_titles=('Profitability', 'Liquidity', 'Leverage', 'Efficiency'))
    years = company_ratios['year']
    fig.add_trace(go.Scatter(x=years, y=company_ratios['roa']*100, name='ROA %'), row=1, col=1)
    fig.add_trace(go.Scatter(x=years, y=company_ratios['roe']*100, name='ROE %'), row=1, col=1)
    fig.add_trace(go.Scatter(x=years, y=company_ratios['current_ratio'], name='Current Ratio'), row=1, col=2)
    fig.add_trace(go.Scatter(x=years, y=company_ratios['debt_to_equity'], name='Debt to Equity'), row=2, col=1)
    fig.add_trace(go.Scatter(x=years, y=company_ratios['inventory_turnover'], name='Inventory Turnover'), row=2, col=2)
    fig.update_layout(height=600, title_text=f"Key Financial Ratios - {company_id}", showlegend=False)
    return fig

def display_qa_findings(qa_df, company_id=None, year=None):
    if qa_df.empty:
        st.info("No QA findings to display.")
        return
    filtered_qa = qa_df.copy()
    if company_id:
        filtered_qa = filtered_qa[filtered_qa['company_id'] == company_id]
    if year:
        filtered_qa = filtered_qa[filtered_qa['year'] == year]
    
    if filtered_qa.empty:
        st.info("No QA findings for the selected filters.")
        return
    
    def severity_color(severity):
        colors = {'high': '🔴', 'medium': '🟡', 'low': '🔵'}
        return colors.get(severity.lower(), '⚪')
    
    for _, finding in filtered_qa.iterrows():
        severity_icon = severity_color(finding['severity'])
        with st.expander(f"{severity_icon} {finding['rule_name']} - {finding['year']}"):
            st.write(f"**Rule ID:** {finding['rule_id']}")
            st.write(f"**Severity:** {finding['severity'].title()}")
            st.write(f"**Details:** {finding['details']}")

def display_banking_insights(data, selected_company_id):
    st.subheader("Free Cash Flow Trends")
    st.info("Free Cash Flow (FCF) = Operating Cash Flow - Capital Expenditures (CapEx)")
    fcf_data = []
    cf_df = data['cashflow'][data['cashflow']['company_id'] == selected_company_id]
    for year in sorted(cf_df['year'].unique()):
        cfo = get_field_value(cf_df, selected_company_id, year, 'cfo')
        capex = get_field_value(cf_df, selected_company_id, year, 'capex')
        if cfo is not None and capex is not None:
            fcf_data.append({'year': year, 'fcf': cfo - capex})
    
    if fcf_data:
        fcf_df = pd.DataFrame(fcf_data)
        fcf_chart = go.Figure()
        fcf_chart.add_trace(go.Scatter(x=fcf_df['year'], y=fcf_df['fcf'], mode='lines+markers', name='Free Cash Flow'))
        fcf_chart.update_layout(title="Free Cash Flow Trend", xaxis_title="Year", yaxis_title="FCF")
        st.plotly_chart(fcf_chart, use_container_width=True)
    else:
        st.warning("Insufficient data for FCF trend.")
    st.subheader("Quality of Earnings")
    st.info("Quality of Earnings is high when Operating Cash Flow consistently exceeds or equals Net Income.")
    income_df = data.get('income', pd.DataFrame())
    cashflow_df = data.get('cashflow', pd.DataFrame())
    
    if not income_df.empty and not cashflow_df.empty:
        qoe_data = []
        for year in get_available_years(data, selected_company_id):
            ni = get_field_value(income_df, selected_company_id, year, 'net_income')
            cfo = get_field_value(cashflow_df, selected_company_id, year, 'cfo')
            if ni is not None and cfo is not None:
                qoe_data.append({'year': year, 'Net Income': ni, 'Operating Cash Flow': cfo})
        if qoe_data:
            qoe_df = pd.DataFrame(qoe_data)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=qoe_df['year'], y=qoe_df['Net Income'], name='Net Income'))
            fig.add_trace(go.Scatter(x=qoe_df['year'], y=qoe_df['Operating Cash Flow'], name='Operating Cash Flow', mode='lines+markers', line=dict(color='orange', width=4)))
            fig.update_layout(title="Net Income vs Operating Cash Flow", barmode='group')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Insufficient data for Quality of Earnings chart.")

def display_prediction_result(result, model_info):
    """Display ML prediction results with enhanced styling"""
    st.markdown("---")
    
    # Main prediction result
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="prediction-result">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <div style="font-size: 2.5rem; margin-right: 1rem;">{model_info['icon']}</div>
                <div>
                    <h3 style="margin: 0; color: #333;">{result['model_name']}</h3>
                    <p style="margin: 0.5rem 0; color: #666;">{model_info['description']}</p>
                </div>
            </div>
            <div style="font-size: 1.8rem; font-weight: bold; color: {model_info['color']};">
                Prediction: {result['prediction']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Confidence meter
        confidence = result['confidence']
        st.metric("Confidence", f"{confidence*100:.1f}%")
        
        # Confidence bar
        confidence_html = f"""
        <div class="confidence-bar">
            <div class="confidence-fill" style="width: {confidence*100}%;">
                <div style="position: absolute; right: 10px; top: 50%; transform: translateY(-50%); 
                          color: white; font-weight: bold; font-size: 0.8rem;">
                    {confidence*100:.1f}%
                </div>
            </div>
        </div>
        """
        st.markdown(confidence_html, unsafe_allow_html=True)
    
    # Features analysis
    st.markdown("#### Model Analysis Details")
    
    col1, col2 = st.columns(2)
    with col1:
        if result.get('features_used'):
            st.markdown('<div class="feature-list">', unsafe_allow_html=True)
            st.markdown("**Features Used:**")
            for feature in result['features_used']:
                st.markdown(f'<div class="feature-used">✅ {feature.replace("_", " ").title()}</div>', 
                          unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        if result.get('missing_features'):
            st.markdown('<div class="feature-list">', unsafe_allow_html=True)
            st.markdown("**Missing Features:**")
            for feature in result['missing_features']:
                st.markdown(f'<div class="feature-missing">❌ {feature.replace("_", " ").title()}</div>', 
                          unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.success("✅ All required features available!")

def ml_predictions_tab():
    """ML Predictions tab"""
    st.markdown("## 🤖 ML Predictions")
    
    if not ML_AVAILABLE:
        st.error("❌ ML functionality is not available. Please ensure mlmodel.py is properly installed.")
        return
    
    # Load financial data
    data = load_financial_data()
    if not data or all(df.empty for df in data.values()):
        st.warning("⚠️ No financial data available. Please upload and process financial reports first.")
        return
    
    # Company and year selection
    companies = get_available_companies(data)
    if not companies:
        st.warning("⚠️ No companies found in the data.")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        selected_company_id = st.selectbox("Select Company", companies, key="ml_company")
    
    with col2:
        available_years = get_available_years(data, selected_company_id)
        if available_years:
            selected_year = st.selectbox("Select Year", available_years, key="ml_year")
        else:
            st.warning("⚠️ No years available for selected company.")
            return
    
    # Get company data for selected year
    company_data = {}
    for data_type in ['income', 'balance', 'cashflow', 'features']:
        if data_type in data and not data[data_type].empty:
            filtered_data = data[data_type][
                (data[data_type]['company_id'] == selected_company_id) & 
                (data[data_type]['year'] == selected_year)
            ]
            company_data[data_type] = filtered_data
        else:
            company_data[data_type] = pd.DataFrame()
    
    # Check if we have sufficient data
    if all(df.empty for df in company_data.values()):
        st.warning(f"⚠️ No data available for {selected_company_id} in {selected_year}")
        return
    
    st.markdown("---")
    
    # Get available ML models
    try:
        available_models = get_available_ml_models()
    except Exception as e:
        st.error(f"❌ Error loading ML models: {e}")
        return
    
    if not available_models:
        st.info("ℹ️ No ML models are currently available. Please ensure your trained models are in the 'models' folder.")
        return
    
    # Display model selection cards
    st.markdown("### Available Prediction Models")
    
    # Create responsive grid layout
    cols = st.columns(min(len(available_models), 3))
    
    for idx, model_info in enumerate(available_models):
        with cols[idx % len(cols)]:
            # Model card with enhanced styling
            st.markdown(f"""
            <div class="ml-card" style="border-left: 5px solid {model_info['color']};">
                <div class="ml-card-header">
                    <div class="ml-card-icon">{model_info['icon']}</div>
                    <div>
                        <div class="ml-card-title">{model_info['name']}</div>
                    </div>
                </div>
                <div class="ml-card-description">{model_info['description']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Model status
            if model_info['is_loaded']:
                st.success("✅ Model Ready")
            else:
                st.error("❌ Model Not Found")
            
            # Prediction button
            if model_info['is_loaded']:
                if st.button(
                    f"🔮 Run {model_info['name']}", 
                    key=f"btn_{model_info['model_key']}", 
                    type="primary",
                    use_container_width=True
                ):
                    with st.spinner(f"Running {model_info['name']}..."):
                        # Prepare financial data for prediction
                        financial_data = {}
                        for data_type in ['features', 'income', 'balance', 'cashflow']:
                            if not company_data[data_type].empty:
                                financial_data[data_type] = company_data[data_type].iloc[0].to_dict()
                            else:
                                financial_data[data_type] = {}
                        
                        # Make prediction
                        result = make_ml_prediction(financial_data, model_info['model_key'])
                        
                        # Display result
                        if result['success']:
                            display_prediction_result(result, model_info)
                        else:
                            st.error(f"❌ Prediction failed: {result.get('error', 'Unknown error')}")

# NEW FUNCTION - Analysis Tab Content
def analysis_tab_content():
    """Power BI Analysis Tab Content"""
    st.header("📊 Financial report")
    
    # Your Power BI Report URL
    powerbi_url = "https://app.powerbi.com/reportEmbed?reportId=b90fcfbc-d5c7-4f99-bbf4-13bc62800297&autoAuth=true&ctid=58cf0878-8e3c-4ef8-b07b-4910aec8f052"
    # Embed the report in an iframe
    st.markdown(
        f"""
        <iframe title="NPN_Dashboard" width="1200" height="700" src="{powerbi_url}" frameborder="0" allowFullScreen="true"></iframe>
        """,
        unsafe_allow_html=True
    )

def main():
    st.markdown('<h1 class="main-header">📊 Unified Financial Analysis Dashboard</h1>', unsafe_allow_html=True)
    
    handle_file_upload_and_pipeline()
    if not os.path.exists('data/output/income.csv'):
        return
    with st.spinner("Loading financial data..."):
        data = load_financial_data()
        
    if not data or all(df.empty for df in data.values()):
        st.error("No financial data available. Please run the pipeline first.")
        return
    
    # Load company name map from JSON
    company_map = load_json('data/output/company_map.json')
    if not company_map:
        st.warning("Company name map not found. Displaying UUIDs.")
        company_id_to_name = {}
    else:
        company_id_to_name = company_map
        
    embeddings_manager = load_embeddings_manager()
    FinancialDataTool.loaded_data = data
    st.sidebar.title("Company & Year Selection")
    
    # Get company IDs and map them to names for display
    company_ids = get_available_companies(data)
    company_names = [company_id_to_name.get(cid, cid) for cid in company_ids]
    
    selected_company_name = st.sidebar.selectbox("Select Company", company_names)
    
    # Get the selected company's UUID from the name
    selected_company_id = next((cid for cid, name in company_id_to_name.items() if name == selected_company_name), selected_company_name)
    
    available_years = get_available_years(data, selected_company_id)
    if not available_years:
        st.error(f"No data available for {selected_company_name}")
        return
    selected_year = st.sidebar.selectbox("Select Year", available_years)
    
    # UPDATED TAB STRUCTURE - Added Analysis tab between ML Predictions and Review Report
    tab_overview, tab_trends, tab_qa, tab_insights, tab_chatbot, tab_ml, tab_analysis, tab_report = st.tabs([
        "📊 Overview", "📈 Financial Trends", "⚠️ QA Findings", "🏦 Banking Insights", "💬 Chatbot Assistant", "🤖 ML Predictions", "📊 Analysis", "📝 Review Report"
    ])
    
    with tab_overview:
        st.header(f"Financial Overview - {selected_company_name} ({selected_year})")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("Income Statement")
            revenue = get_field_value(data['income'], selected_company_id, selected_year, 'revenue')
            net_income = get_field_value(data['income'], selected_company_id, selected_year, 'net_income')
            st.metric("Revenue", f"${revenue:,.0f}" if revenue is not None else "N/A")
            st.metric("Net Income", f"${net_income:,.0f}" if net_income is not None else "N/A")
        with col2:
            st.subheader("Balance Sheet")
            total_assets = get_field_value(data['balance'], selected_company_id, selected_year, 'total_assets')
            total_equity = get_field_value(data['balance'], selected_company_id, selected_year, 'total_equity')
            st.metric("Total Assets", f"${total_assets:,.0f}" if total_assets is not None else "N/A")
            st.metric("Total Equity", f"${total_equity:,.0f}" if total_equity is not None else "N/A")
        with col3:
            st.subheader("Cash Flow")
            cfo = get_field_value(data['cashflow'], selected_company_id, selected_year, 'cfo')
            st.metric("Operating Cash Flow", f"${cfo:,.0f}" if cfo is not None else "N/A")
    
    with tab_trends:
        st.header(f"Financial Trends - {selected_company_name}")
        ratios_chart = create_ratios_chart(data['features'], selected_company_id)
        if ratios_chart:
            st.plotly_chart(ratios_chart, use_container_width=True)
        st.subheader("Individual Metric Trends")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_trend_chart(data['income'], selected_company_id, 'revenue', 'Revenue Trend'), use_container_width=True)
        with col2:
            st.plotly_chart(create_trend_chart(data['balance'], selected_company_id, 'total_assets', 'Total Assets Trend'), use_container_width=True)
    
    with tab_qa:
        st.header("Quality Assurance Findings")
        display_qa_findings(data['qa_findings'], selected_company_id, selected_year)
    
    with tab_insights:
        st.header("Banking & Credit Insights")
        display_banking_insights(data, selected_company_id)
    
    with tab_chatbot:
        st.header("AI-Powered Q&A from Financial Notes")
        if embeddings_manager is None:
            st.warning("Vector embeddings not available. Please run the pipeline with notes data.")
        else:
            query = st.text_area("Enter your question:", placeholder="e.g., What are the main risk factors mentioned?", key="chatbot_query")
            if st.button("🔍 Get Answer", type="primary", key="chatbot_button") and query.strip():
                with st.spinner("Searching financial documents..."):
                    results = embeddings_manager.semantic_search(query=query, top_k=5, company_filter=selected_company_id, year_filter=selected_year)
                    
                    if not results:
                        st.info("No relevant information found for the query.")
                    else:
                        ai_answer = generate_answer_from_context(query, results)
                        st.subheader("🤖 AI Generated Answer")
                        st.markdown(ai_answer)
                        
                        st.subheader("📄 Source Documents")
                        for i, result in enumerate(results):
                            with st.expander(f"Source {i+1}: {result['year']} - {result['section']} (Score: {result['score']:.3f})"):
                                st.write(result['text'])
    
    with tab_ml:
        ml_predictions_tab()
    
    # NEW ANALYSIS TAB - Added your Power BI dashboard
    with tab_analysis:
        analysis_tab_content()
    
    with tab_report:
        st.header("AI-Generated Review Report")
        if st.button("📝 Generate Full Analysis Report", key="generate_report_btn"):
            with st.spinner("Running AI agents to generate the report..."):
                report_text = run_analysis_crew(task_inputs={"company_id": selected_company_id, "company_name": selected_company_name})
                st.session_state.report_text = report_text
        if st.session_state.get("report_text"):
            st.markdown("### ✅ Report Complete")
            st.markdown(st.session_state.report_text)
            st.download_button(
                label="Download Report",
                data=st.session_state.report_text,
                file_name=f"{selected_company_id}_financial_report.md",
                mime="text/markdown"
            )

if __name__ == "__main__":
    main()

# mlmodel.py - Fixed version with EXACT training order
"""
ML Models for Financial Analysis Predictions
Handles loading of pre-trained models and making predictions using financial features
"""

import os
import pickle
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Any, Tuple
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialMLPredictor:
    """
    Manages pre-trained ML models for financial predictions
    """
    
    def __init__(self, models_dir: str = 'models'):
        self.models_dir = models_dir
        self.models = {}
        self.model_configs = {}
        self.available_models = []
        
        # Ensure models directory exists
        os.makedirs(models_dir, exist_ok=True)
        
        # Initialize model configurations for your actual trained models
        self._initialize_model_configs()
        
        # Load available models
        self._discover_models()
    
    def _initialize_model_configs(self):
        """Initialize model configurations based on your actual trained models"""
        self.model_configs = {
            'fraud_risk_model': {
                'name': 'Fraud Risk Detection',
                'description': 'Identifies potential financial irregularities and fraud indicators',
                'type': 'classification',
                'icon': '🔍',
                'color': '#FF6B6B',
                'output_label': 'Fraud Risk',
                'output_format': 'risk_level',
                'model_filename': 'fraud_risk_model.pkl',
                'required_features': [
                    'gross_margin', 'operating_margin', 'net_margin', 'roa', 'roe',
                    'current_ratio', 'quick_ratio', 'debt_to_equity', 'interest_coverage',
                    'accrual_ratio', 'cfo_net_income_ratio', 'accounts_receivable_growth',
                    'revenue_growth', 'inventory_growth'
                ]
            },
            'liquidity_risk_model': {
                'name': 'Liquidity Risk Prediction',
                'description': 'Predicts liquidity risk using key financial ratios and performance indicators',
                'type': 'classification',
                'icon': '💧',
                'color': '#36A2EB',
                'output_label': 'Liquidity Risk',
                'output_format': 'risk_level',
                'model_filename': 'liquidity_risk_model.pkl',
                # ✅ FIXED: Exact order from your training data
                'required_features': [
                    'gross_margin',                    # 1
                    'operating_margin',               # 2
                    'net_margin',                     # 3
                    'roa',                           # 4
                    'roe',                           # 5
                    'current_ratio',                 # 6
                    'quick_ratio',                   # 7
                    'debt_to_equity',                # 8
                    'interest_coverage',             # 9
                    'accrual_ratio',                 # 10
                    'cfo_net_income_ratio',          # 11
                    'accounts_receivable_growth',    # 12
                    'revenue_growth',                # 13
                    'inventory_growth'               # 14
                ]
            },
            'EWS_model': {
                'name': 'Early Warning System',
                'description': 'Early warning system with 25 key financial indicators',
                'type': 'classification',
                'icon': '🚨',
                'color': '#FF9F40',
                'output_label': 'Warning Level',
                'output_format': 'warning_level',
                'model_filename': 'EWS.pkl',
                'required_features': [
                    'current_ratio', 'debt_to_equity', 'roa', 'roe', 'operating_margin',
                    'net_margin', 'gross_margin', 'interest_coverage', 'cfo_to_net_income',
                    'inventory_turnover', 'receivables_days', 'revenue_growth', 'asset_turnover',
                    'quick_ratio', 'cash_ratio', 'working_capital_ratio', 'total_assets',
                    'total_liabilities', 'revenue', 'net_income', 'cfo', 'capex',
                    'debt_service_coverage', 'times_interest_earned', 'price_to_book'
                ]
            }
        }
    
    def _discover_models(self):
        """Discover available trained models in the models directory"""
        self.available_models = []
        
        if not os.path.exists(self.models_dir):
            logger.warning(f"Models directory {self.models_dir} does not exist")
            return
        
        for model_key, config in self.model_configs.items():
            model_filename = config['model_filename']
            model_file = os.path.join(self.models_dir, model_filename)
            
            if os.path.exists(model_file):
                try:
                    with open(model_file, 'rb') as f:
                        model = pickle.load(f)
                    
                    # Validate that loaded object has predict method
                    if hasattr(model, 'predict'):
                        self.models[model_key] = model
                        self.available_models.append(model_key)
                        logger.info(f"Loaded model: {model_key} from {model_filename}")
                    else:
                        logger.error(f"Loaded object from {model_filename} is not a valid model (no predict method). Type: {type(model)}")
                        
                except Exception as e:
                    logger.error(f"Failed to load model {model_key} from {model_filename}: {e}")
            else:
                logger.warning(f"Model file not found: {model_file}")
        
        logger.info(f"Total models loaded: {len(self.available_models)}")
    
    def get_available_models(self) -> List[Dict]:
        """Get list of available models with their metadata"""
        available = []
        for model_key in self.model_configs.keys():
            config = self.model_configs[model_key].copy()
            config['model_key'] = model_key
            config['is_loaded'] = model_key in self.models
            available.append(config)
        return available
    
    def _safe_get(self, data_dict: Dict, key: str, default: float = 0.0) -> float:
        """Safely get value from nested financial data"""
        # Check all data sources
        for source in ['features', 'income', 'balance', 'cashflow']:
            if source in data_dict and key in data_dict[source]:
                value = data_dict[source][key]
                if pd.notna(value) and value is not None:
                    return float(value)
        return default
    
    def _calculate_derived_features(self, financial_data: Dict) -> Dict:
        """Calculate derived features that models might need"""
        derived = {}
        
        # Get base values
        revenue = self._safe_get(financial_data, 'revenue')
        net_income = self._safe_get(financial_data, 'net_income')
        total_assets = self._safe_get(financial_data, 'total_assets')
        total_equity = self._safe_get(financial_data, 'total_equity')
        total_liabilities = self._safe_get(financial_data, 'total_liabilities')
        current_assets = self._safe_get(financial_data, 'total_current_assets')
        current_liabilities = self._safe_get(financial_data, 'total_current_liabilities')
        cash = self._safe_get(financial_data, 'cash_and_equivalents')
        gross_profit = self._safe_get(financial_data, 'gross_profit')
        operating_income = self._safe_get(financial_data, 'operating_income')
        cfo = self._safe_get(financial_data, 'cfo')
        accounts_receivable = self._safe_get(financial_data, 'accounts_receivable')
        inventory = self._safe_get(financial_data, 'inventory')
        interest_expense = self._safe_get(financial_data, 'interest_expense')
        pretax_income = self._safe_get(financial_data, 'pretax_income')
        
        # ✅ CRITICAL: Calculate ALL required features in the EXACT training order
        derived.update({
            # Margins (positions 1-3)
            'gross_margin': gross_profit / revenue if revenue else 0.0,
            'operating_margin': operating_income / revenue if revenue else 0.0,
            'net_margin': net_income / revenue if revenue else 0.0,
            
            # Profitability ratios (positions 4-5)
            'roa': net_income / total_assets if total_assets else 0.0,
            'roe': net_income / total_equity if total_equity else 0.0,
            
            # Liquidity ratios (positions 6-7)
            'current_ratio': current_assets / current_liabilities if current_liabilities else 1.0,
            'quick_ratio': (current_assets - inventory) / current_liabilities if current_liabilities else 1.0,
            
            # Leverage ratios (positions 8-9)
            'debt_to_equity': total_liabilities / total_equity if total_equity else 0.0,
            'interest_coverage': (pretax_income + interest_expense) / interest_expense if interest_expense else 1.0,
            
            # Complex ratios (positions 10-11)
            'accrual_ratio': 0.0,  # Default complex calculation
            'cfo_net_income_ratio': cfo / net_income if net_income else 0.0,
            
            # Growth rates (positions 12-14) - defaulted since no historical data
            'accounts_receivable_growth': 0.0,
            'revenue_growth': 0.0,
            'inventory_growth': 0.0,
            
            # Additional features for other models
            'cfo_to_net_income': cfo / net_income if net_income else 0.0,
            'asset_turnover': revenue / total_assets if total_assets else 0.0,
            'inventory_turnover': 0.0,
            'receivables_days': 0.0,
            'working_capital_ratio': (current_assets - current_liabilities) / total_assets if total_assets else 0.0,
            'debt_service_coverage': 0.0,
            'times_interest_earned': (pretax_income + interest_expense) / interest_expense if interest_expense else 0.0,
            'price_to_book': 0.0,
            'capex': 0.0,
            'cash_ratio': cash / current_liabilities if current_liabilities else 0.0,
            
            # Raw values for models that need them
            'revenue': revenue,
            'net_income': net_income,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'cfo': cfo
        })
        
        return derived
    
    def prepare_features(self, financial_data: Dict, model_key: str) -> Tuple[pd.DataFrame, List[str]]:
        """Prepare features for a specific model from financial data"""
        if model_key not in self.model_configs:
            raise ValueError(f"Unknown model: {model_key}")
        
        config = self.model_configs[model_key]
        required_features = config['required_features']
        
        # Calculate derived features
        derived_features = self._calculate_derived_features(financial_data)
        
        # Combine all available data
        all_data = {}
        for source in ['features', 'income', 'balance', 'cashflow']:
            if source in financial_data and financial_data[source]:
                all_data.update(financial_data[source])
        all_data.update(derived_features)
        
        features_dict = {}
        missing_features = []
        
        # ✅ CRITICAL: Build features in EXACT training order
        for feature in required_features:
            if feature in all_data and pd.notna(all_data[feature]) and all_data[feature] is not None:
                features_dict[feature] = float(all_data[feature])
            else:
                # Set appropriate defaults based on feature type
                if feature == 'roe':
                    features_dict[feature] = 0.0
                elif feature == 'accounts_receivable_growth':
                    features_dict[feature] = 0.0
                elif 'ratio' in feature.lower() or 'coverage' in feature.lower():
                    features_dict[feature] = 1.0  # Better default for ratios
                elif 'growth' in feature.lower():
                    features_dict[feature] = 0.0
                elif 'margin' in feature.lower():
                    features_dict[feature] = 0.0
                elif feature in ['roa', 'roe']:
                    features_dict[feature] = 0.0
                elif 'flag' in feature.lower():
                    features_dict[feature] = 0
                else:
                    features_dict[feature] = 0.0
                missing_features.append(feature)
        
        # ✅ CRITICAL: Create DataFrame maintaining EXACT training order
        features_df = pd.DataFrame([features_dict])
        
        # ✅ CRITICAL: Reindex to ensure exact column order matches training
        features_df = features_df.reindex(columns=required_features, fill_value=0.0)
        
        # ✅ CRITICAL: Final verification
        for feature in required_features:
            if feature not in features_df.columns:
                features_df[feature] = 0.0
                logger.warning(f"Added missing feature {feature} with default value 0.0")
        
        # Log the final feature order for debugging
        logger.info(f"Final feature order for {model_key}: {list(features_df.columns)}")
        
        return features_df, missing_features
    
    def make_prediction(self, financial_data: Dict, model_key: str) -> Dict[str, Any]:
        """Make prediction using specified model"""
        if model_key not in self.available_models:
            return {
                'success': False,
                'error': f'Model {model_key} not available',
                'available_models': self.available_models
            }
        
        try:
            # Prepare features
            features_df, missing_features = self.prepare_features(financial_data, model_key)
            
            # Get model and configuration
            model = self.models[model_key]
            config = self.model_configs[model_key]
            
            # Validate model object before prediction
            if not hasattr(model, 'predict'):
                return {
                    'success': False,
                    'error': f'Model {model_key} does not have predict method. Type: {type(model)}',
                    'model_key': model_key
                }
            
            # Make prediction
            if config['type'] == 'classification':
                prediction = model.predict(features_df)[0]
                if hasattr(model, 'predict_proba'):
                    try:
                        probabilities = model.predict_proba(features_df)[0]
                        confidence = float(np.max(probabilities))
                    except:
                        confidence = 0.85  # Default confidence
                else:
                    confidence = 0.85  # Default confidence
            else:  # regression
                prediction = float(model.predict(features_df)[0])
                confidence = 0.85  # Default confidence for regression
            
            # Format output based on model type
            formatted_prediction = self._format_prediction(prediction, config)
            
            return {
                'success': True,
                'model_name': config['name'],
                'model_key': model_key,
                'prediction': formatted_prediction,
                'confidence': confidence,
                'missing_features': missing_features,
                'features_used': list(features_df.columns),
                'raw_prediction': prediction
            }
            
        except Exception as e:
            logger.error(f"Prediction error for {model_key}: {e}")
            return {
                'success': False,
                'error': str(e),
                'model_key': model_key
            }
    
    def _format_prediction(self, prediction: Any, config: Dict) -> str:
        """Format prediction based on model configuration"""
        output_format = config.get('output_format', 'raw')
        
        if output_format == 'percentage':
            if isinstance(prediction, (int, float)):
                return f"{prediction * 100:.1f}%"
            return f"{float(prediction) * 100:.1f}%"
        
        elif output_format == 'risk_level':
            if isinstance(prediction, (int, np.integer)):
                risk_map = {0: 'Low Risk', 1: 'Medium Risk', 2: 'High Risk', 3: 'Critical Risk'}
                return risk_map.get(int(prediction), f'Risk Level {prediction}')
            return str(prediction)
        
        elif output_format == 'warning_level':
            if isinstance(prediction, (int, np.integer)):
                warning_map = {0: 'Green', 1: 'Yellow', 2: 'Orange', 3: 'Red Alert'}
                return warning_map.get(int(prediction), f'Warning Level {prediction}')
            return str(prediction)
        
        else:  # raw format
            if isinstance(prediction, (int, float, np.number)):
                return f"{prediction:.2f}"
            return str(prediction)


# Global functions for easy import
_predictor_instance = None

def get_predictor(models_dir: str = 'models'):
    """Get or create global predictor instance"""
    global _predictor_instance
    
    if _predictor_instance is None:
        _predictor_instance = FinancialMLPredictor(models_dir)
    
    return _predictor_instance

def make_ml_prediction(financial_data: Dict, model_key: str) -> Dict[str, Any]:
    """Main function to make ML predictions - used by dashboard"""
    predictor = get_predictor()
    return predictor.make_prediction(financial_data, model_key)

def get_available_ml_models() -> List[Dict]:
    """Get list of available ML models - used by dashboard"""
    predictor = get_predictor()
    return predictor.get_available_models()

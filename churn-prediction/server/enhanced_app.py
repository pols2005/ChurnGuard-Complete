# ChurnGuard Enhanced Flask API with ML Pipeline
# Epic 2 - Advanced ML Pipeline Implementation

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from typing import Dict, Any

# Import ML Pipeline components
from ml_pipeline import (
    ModelRegistry, 
    ABTestingFramework, 
    ModelPerformanceMonitor,
    EnhancedPredictionService,
    PredictionRequest
)
from ml_pipeline.training_pipeline import AutomatedTrainingPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = Flask(__name__)
CORS(app)

# Initialize ML Pipeline components
registry = ModelRegistry()
ab_testing = ABTestingFramework(registry)
monitor = ModelPerformanceMonitor(registry)
prediction_service = EnhancedPredictionService(registry, ab_testing)
training_pipeline = AutomatedTrainingPipeline(registry)

# Legacy model loading for backward compatibility
def load_legacy_models():
    """Load existing pickle models into the new registry"""
    import pickle
    
    legacy_models = {
        'XGBoost': 'xgb_model.pkl',
        'KNeighbors': 'knn_model.pkl', 
        'GBoosting': 'gb_model.pkl',
        'ExtraTrees': 'et_model.pkl',
        'AdaBoost': 'ab_model.pkl'
    }
    
    # Standard features for ChurnGuard
    features = [
        'CreditScore', 'Age', 'Tenure', 'Balance', 'NumOfProducts',
        'HasCrCard', 'IsActiveMember', 'EstimatedSalary',
        'Geography_France', 'Geography_Germany', 'Geography_Spain',
        'Gender_Male', 'Gender_Female'
    ]
    
    # Load test data for registration
    if os.path.exists('churn.csv'):
        df = pd.read_csv('churn.csv')
        X = df.drop(columns=['Exited'])
        y = df['Exited']
        
        # Prepare features same as in original app
        categorical_columns = X.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            if col in ['Geography', 'Gender']:
                dummies = pd.get_dummies(X[col], prefix=col, drop_first=False)
                X = pd.concat([X.drop(columns=[col]), dummies], axis=1)
        
        # Remove non-feature columns
        columns_to_remove = ['RowNumber', 'CustomerId', 'Surname']
        X = X.drop(columns=[col for col in columns_to_remove if col in X.columns])
        
        # Take a sample for testing
        X_test = X.sample(n=min(1000, len(X)), random_state=42)
        y_test = y.loc[X_test.index]
        
        for model_name, filename in legacy_models.items():
            if os.path.exists(filename):
                try:
                    with open(filename, 'rb') as f:
                        model = pickle.load(f)
                    
                    # Register in new system
                    model_key = registry.register_model(
                        model=model,
                        model_id=model_name.lower(),
                        algorithm=model_name.lower(),
                        X_test=X_test,
                        y_test=y_test,
                        features=list(X_test.columns),
                        tags=['legacy_import', 'production_ready'],
                        created_by='legacy_import'
                    )
                    
                    # Promote to production
                    registry.promote_model(model_key, 'production')
                    logger.info(f"Imported and promoted legacy model: {model_key}")
                    
                except Exception as e:
                    logger.error(f"Failed to import {model_name}: {str(e)}")

# Load legacy models on startup
load_legacy_models()

# Helper functions
def prepare_input_features(credit_score, location, gender, age, tenure, balance, 
                          num_products, has_credit_card, is_active_member, estimated_salary):
    """Prepare input features for prediction (backward compatibility)"""
    return {
        'CreditScore': credit_score,
        'Age': age,
        'Tenure': tenure,
        'Balance': balance,
        'NumOfProducts': num_products,
        'HasCrCard': int(has_credit_card),
        'IsActiveMember': int(is_active_member),
        'EstimatedSalary': estimated_salary,
        'Geography_France': 1 if location == 'France' else 0,
        'Geography_Germany': 1 if location == 'Germany' else 0,
        'Geography_Spain': 1 if location == 'Spain' else 0,
        'Gender_Male': 1 if gender == 'Male' else 0,
        'Gender_Female': 1 if gender == 'Female' else 0
    }

# ========== LEGACY API ENDPOINTS (Backward Compatibility) ==========

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Get list of all customers (legacy endpoint)"""
    try:
        df = pd.read_csv('churn.csv')
        customers = df[['CustomerId', 'Surname']].to_dict(orient='records')
        return jsonify(customers)
    except Exception as e:
        logger.error(f"Error getting customers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/customer/<int:customer_id>', methods=['GET'])
def get_customer_details(customer_id):
    """Get customer details by ID (legacy endpoint)"""
    try:
        df = pd.read_csv('churn.csv')
        customer = df[df['CustomerId'] == customer_id].to_dict(orient='records')
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        return jsonify({'customer': customer[0]})
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/customer/<int:customer_id>/churn-probability', methods=['GET'])
def get_average_churn_probability(customer_id):
    """Get average churn probability (enhanced with new pipeline)"""
    try:
        df = pd.read_csv('churn.csv')
        customer = df[df['CustomerId'] == customer_id].to_dict(orient='records')
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        customer = customer[0]
        
        # Prepare features
        features = prepare_input_features(
            customer['CreditScore'], customer['Geography'], customer['Gender'],
            customer['Age'], customer['Tenure'], customer['Balance'],
            customer['NumOfProducts'], customer['HasCrCard'],
            customer['IsActiveMember'], customer['EstimatedSalary']
        )
        
        # Create prediction request
        pred_request = PredictionRequest(
            customer_id=str(customer_id),
            features=features,
            include_confidence=True
        )
        
        # Get prediction using enhanced service
        response = prediction_service.predict_single(pred_request)
        
        # Record for monitoring
        monitor.record_prediction(
            model_key=response.model_used,
            customer_id=str(customer_id),
            prediction=response.prediction,
            response_time_ms=response.response_time_ms,
            features=features,
            actual_outcome=customer.get('Exited')  # If available
        )
        
        return jsonify({
            'customer_id': customer_id,
            'average_probability': response.prediction,
            'confidence': response.confidence,
            'model_used': response.model_used,
            'response_time_ms': response.response_time_ms
        })
        
    except Exception as e:
        logger.error(f"Error getting churn probability for customer {customer_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ========== ENHANCED ML PIPELINE ENDPOINTS ==========

@app.route('/api/v2/predict', methods=['POST'])
def enhanced_predict():
    """Enhanced prediction endpoint with A/B testing support"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'customer_id' not in data or 'features' not in data:
            return jsonify({'error': 'customer_id and features are required'}), 400
        
        # Create prediction request
        pred_request = PredictionRequest(
            customer_id=data['customer_id'],
            features=data['features'],
            model_id=data.get('model_id'),
            ab_test_id=data.get('ab_test_id'),
            include_explanation=data.get('include_explanation', False),
            include_confidence=data.get('include_confidence', True)
        )
        
        # Get prediction
        response = prediction_service.predict_single(pred_request)
        
        # Record for monitoring
        monitor.record_prediction(
            model_key=response.model_used,
            customer_id=response.customer_id,
            prediction=response.prediction,
            response_time_ms=response.response_time_ms,
            features=data['features']
        )
        
        return jsonify({
            'customer_id': response.customer_id,
            'prediction': response.prediction,
            'confidence': response.confidence,
            'model_used': response.model_used,
            'prediction_time': response.prediction_time,
            'response_time_ms': response.response_time_ms,
            'feature_importance': response.feature_importance
        })
        
    except Exception as e:
        logger.error(f"Error in enhanced prediction: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/predict/batch', methods=['POST'])
def batch_predict():
    """Batch prediction endpoint"""
    try:
        data = request.get_json()
        
        if 'requests' not in data:
            return jsonify({'error': 'requests array is required'}), 400
        
        # Create prediction requests
        requests = []
        for req_data in data['requests']:
            pred_request = PredictionRequest(
                customer_id=req_data['customer_id'],
                features=req_data['features'],
                model_id=req_data.get('model_id'),
                ab_test_id=req_data.get('ab_test_id'),
                include_confidence=req_data.get('include_confidence', True)
            )
            requests.append(pred_request)
        
        # Get batch predictions
        responses = prediction_service.predict_batch(requests)
        
        # Record for monitoring
        for response in responses:
            if response.model_used != "error":
                req_data = next((r for r in data['requests'] if r['customer_id'] == response.customer_id), {})
                monitor.record_prediction(
                    model_key=response.model_used,
                    customer_id=response.customer_id,
                    prediction=response.prediction,
                    response_time_ms=response.response_time_ms,
                    features=req_data.get('features', {})
                )
        
        return jsonify({
            'responses': [
                {
                    'customer_id': r.customer_id,
                    'prediction': r.prediction,
                    'confidence': r.confidence,
                    'model_used': r.model_used,
                    'response_time_ms': r.response_time_ms
                } for r in responses
            ]
        })
        
    except Exception as e:
        logger.error(f"Error in batch prediction: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def list_models():
    """List all models in the registry"""
    try:
        status = request.args.get('status')
        model_id = request.args.get('model_id')
        
        models = registry.list_models(model_id=model_id, status=status)
        
        return jsonify({
            'models': [
                {
                    'model_id': m.model_id,
                    'version': m.version,
                    'algorithm': m.algorithm,
                    'training_date': m.training_date,
                    'deployment_status': m.deployment_status,
                    'performance_metrics': m.performance_metrics,
                    'created_by': m.created_by
                } for m in models
            ]
        })
        
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/<model_key>/promote', methods=['POST'])
def promote_model(model_key):
    """Promote model to different deployment status"""
    try:
        data = request.get_json()
        target_status = data.get('target_status', 'staging')
        
        registry.promote_model(model_key, target_status)
        
        return jsonify({
            'message': f'Model {model_key} promoted to {target_status}',
            'model_key': model_key,
            'target_status': target_status
        })
        
    except Exception as e:
        logger.error(f"Error promoting model {model_key}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ab-tests', methods=['POST'])
def create_ab_test():
    """Create A/B test"""
    try:
        data = request.get_json()
        
        test_id = ab_testing.create_ab_test(
            test_name=data['test_name'],
            model_a=data['model_a'],
            model_b=data['model_b'],
            traffic_split=data.get('traffic_split', 0.5),
            duration_days=data.get('duration_days', 30),
            success_metric=data.get('success_metric', 'accuracy'),
            description=data.get('description', ''),
            created_by=data.get('created_by', 'api_user')
        )
        
        return jsonify({
            'test_id': test_id,
            'message': 'A/B test created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating A/B test: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ab-tests/<test_id>/analyze', methods=['GET'])
def analyze_ab_test(test_id):
    """Analyze A/B test results"""
    try:
        analysis = ab_testing.analyze_test(test_id)
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing A/B test {test_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/health', methods=['GET'])
def monitoring_health():
    """Get overall monitoring health"""
    try:
        summary = monitor.get_monitoring_summary()
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting monitoring health: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/models/<model_key>', methods=['GET'])
def model_health(model_key):
    """Get health status for specific model"""
    try:
        health = monitor.get_model_health(model_key)
        return jsonify(health)
        
    except Exception as e:
        logger.error(f"Error getting model health for {model_key}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/alerts', methods=['GET'])
def get_alerts():
    """Get recent alerts"""
    try:
        severity = request.args.get('severity')
        hours = int(request.args.get('hours', 24))
        
        alerts = monitor.get_alerts(severity=severity, hours=hours)
        
        return jsonify({
            'alerts': [
                {
                    'alert_id': a.alert_id,
                    'timestamp': a.timestamp,
                    'model_key': a.model_key,
                    'drift_type': a.drift_type,
                    'severity': a.severity,
                    'description': a.description,
                    'recommended_action': a.recommended_action
                } for a in alerts
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/training/train', methods=['POST'])
def trigger_training():
    """Trigger automated model training"""
    try:
        data = request.get_json()
        
        # Create training config
        config = training_pipeline.create_training_config(
            model_id=data['model_id'],
            training_data_path=data.get('training_data_path', 'churn.csv'),
            algorithms=data.get('algorithms', ['xgboost', 'random_forest']),
            hyperparameter_tuning=data.get('hyperparameter_tuning', True),
            created_by=data.get('created_by', 'api_user')
        )
        
        # Run training pipeline
        results = training_pipeline.run_training_pipeline(config)
        
        return jsonify({
            'message': 'Training completed',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in training pipeline: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/service/stats', methods=['GET'])
def service_stats():
    """Get prediction service statistics"""
    try:
        stats = prediction_service.get_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting service stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/service/healthcheck', methods=['GET'])
def service_healthcheck():
    """Enhanced service health check"""
    try:
        health = prediction_service.healthcheck()
        return jsonify(health)
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Update outcome endpoint for monitoring
@app.route('/api/monitoring/outcome', methods=['POST'])
def update_outcome():
    """Update actual outcome for monitoring"""
    try:
        data = request.get_json()
        customer_id = data['customer_id']
        actual_outcome = data['actual_outcome']
        
        monitor.update_actual_outcome(customer_id, actual_outcome)
        
        # Also update A/B test if test_id provided
        if 'ab_test_id' in data:
            ab_testing.update_outcome(customer_id, data['ab_test_id'], actual_outcome)
        
        return jsonify({'message': 'Outcome updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating outcome: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Graceful shutdown
import atexit
def cleanup():
    """Cleanup resources on shutdown"""
    logger.info("Shutting down ML pipeline services...")
    prediction_service.shutdown()

atexit.register(cleanup)

if __name__ == '__main__':
    logger.info("Starting ChurnGuard Enhanced ML Pipeline API...")
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
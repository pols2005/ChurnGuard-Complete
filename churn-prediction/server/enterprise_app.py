# ChurnGuard Enterprise Flask API with Authentication
# Epic 3 - Enterprise Features & Multi-Tenancy

from flask import Flask, jsonify, request, g
from flask_cors import CORS
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os
import logging
import psycopg2
from datetime import datetime
from typing import Dict, Any, Optional

# Import ML Pipeline components
from ml_pipeline import (
    ModelRegistry, 
    ABTestingFramework, 
    ModelPerformanceMonitor,
    EnhancedPredictionService,
    PredictionRequest
)
from ml_pipeline.training_pipeline import AutomatedTrainingPipeline

# Import Enterprise components
from enterprise.authentication_service import AuthenticationService
from enterprise.organization_service import OrganizationService
from enterprise.auth_middleware import AuthenticationMiddleware, require_auth, require_permission, require_api_key
from enterprise.auth_routes import create_auth_blueprint
from enterprise.models import CustomerStatus, ChurnRiskLevel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/churnguard")

def create_app():
    """Application factory with enterprise features"""
    app = Flask(__name__)
    CORS(app, supports_credentials=True)  # Enable credentials for cookies
    
    # Configure app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    
    # Database connection
    try:
        db_connection = psycopg2.connect(DATABASE_URL)
        logger.info("Connected to PostgreSQL database")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        # For development, create a mock connection
        db_connection = None
    
    # Initialize services
    org_service = OrganizationService(db_connection) if db_connection else None
    auth_service = AuthenticationService(db_connection, org_service) if db_connection else None
    auth_middleware = AuthenticationMiddleware(auth_service, org_service) if auth_service else None
    
    # Store services in app context
    app.db = db_connection
    app.org_service = org_service
    app.auth_service = auth_service
    app.auth_middleware = auth_middleware
    
    # Initialize ML Pipeline components
    registry = ModelRegistry()
    ab_testing = ABTestingFramework(registry)
    monitor = ModelPerformanceMonitor(registry)
    prediction_service = EnhancedPredictionService(registry, ab_testing)
    training_pipeline = AutomatedTrainingPipeline(registry)
    
    # Store ML components
    app.ml_registry = registry
    app.ml_ab_testing = ab_testing
    app.ml_monitor = monitor
    app.ml_prediction_service = prediction_service
    app.ml_training_pipeline = training_pipeline
    
    # Load legacy models for backward compatibility
    load_legacy_models(registry)
    
    # ==================== AUTHENTICATION ROUTES ====================
    
    if auth_service and org_service:
        auth_bp = create_auth_blueprint(auth_service, org_service)
        app.register_blueprint(auth_bp)
    
    # ==================== HEALTH CHECK ====================
    
    @app.route('/api/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '3.0.0-enterprise',
            'features': {
                'authentication': auth_service is not None,
                'multi_tenancy': org_service is not None,
                'ml_pipeline': True,
                'database': db_connection is not None
            }
        })
    
    # ==================== LEGACY ENDPOINTS (v1) ====================
    
    @app.route('/predict', methods=['POST'])
    def legacy_predict():
        """Legacy prediction endpoint for backward compatibility"""
        try:
            # Get customer data
            customer_data = request.get_json()
            if not customer_data:
                return jsonify({'error': 'No data provided'}), 400
            
            # Convert to prediction request
            pred_request = PredictionRequest(
                customer_id=customer_data.get('customer_id', 'unknown'),
                features=customer_data
            )
            
            # Make prediction using legacy model
            result = prediction_service.predict(pred_request, model_name='XGBoost')
            
            return jsonify({
                'prediction': result.prediction,
                'probability': result.probability,
                'model': result.model_name,
                'timestamp': result.timestamp.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Legacy prediction error: {e}")
            return jsonify({'error': 'Prediction failed'}), 500
    
    # ==================== MULTI-TENANT PREDICTION ENDPOINTS (v2) ====================
    
    @app.route('/api/v2/predict', methods=['POST'])
    @require_auth
    @require_permission('prediction.create')
    def enterprise_predict():
        """Enterprise prediction with multi-tenancy and RBAC"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            user = g.current_user
            org = g.current_organization
            
            # Validate customer belongs to organization
            customer_id = data.get('customer_id')
            if customer_id:
                customer = get_customer_by_id(org.id, customer_id)
                if not customer:
                    return jsonify({'error': 'Customer not found'}), 404
            
            # Create prediction request
            pred_request = PredictionRequest(
                customer_id=customer_id or 'manual',
                features=data.get('features', {}),
                ab_test_id=data.get('ab_test_id'),
                organization_id=org.id,
                requested_by=user.id
            )
            
            # Make prediction
            result = prediction_service.predict(pred_request, model_name=data.get('model'))
            
            # Store prediction in database if customer exists
            if customer_id and customer:
                store_prediction_result(org.id, customer_id, result, user.id)
            
            # Log prediction event
            org_service._log_audit_event(
                org.id, 'prediction_made', 'customer', customer_id,
                user_id=user.id, user_email=user.email,
                event_data={
                    'model': result.model_name,
                    'prediction': result.prediction,
                    'probability': result.probability
                }
            )
            
            return jsonify({
                'success': True,
                'prediction': result.prediction,
                'probability': result.probability,
                'confidence': result.confidence,
                'model': result.model_name,
                'model_version': result.model_version,
                'timestamp': result.timestamp.isoformat(),
                'ab_test': {
                    'test_id': result.ab_test_id,
                    'variant': result.model_variant
                } if result.ab_test_id else None
            })
            
        except Exception as e:
            logger.error(f"Enterprise prediction error: {e}")
            return jsonify({'error': 'Prediction failed'}), 500
    
    @app.route('/api/v2/predict/batch', methods=['POST'])
    @require_auth
    @require_permission('prediction.create')
    def batch_predict():
        """Batch prediction for multiple customers"""
        try:
            data = request.get_json()
            if not data or 'customers' not in data:
                return jsonify({'error': 'Customers data required'}), 400
            
            user = g.current_user
            org = g.current_organization
            
            customers = data['customers']
            if len(customers) > 1000:  # Limit batch size
                return jsonify({'error': 'Batch size limited to 1000 customers'}), 400
            
            results = []
            
            for customer_data in customers:
                try:
                    pred_request = PredictionRequest(
                        customer_id=customer_data.get('customer_id', 'batch'),
                        features=customer_data.get('features', {}),
                        organization_id=org.id,
                        requested_by=user.id
                    )
                    
                    result = prediction_service.predict(pred_request)
                    
                    results.append({
                        'customer_id': customer_data.get('customer_id'),
                        'prediction': result.prediction,
                        'probability': result.probability,
                        'model': result.model_name,
                        'timestamp': result.timestamp.isoformat()
                    })
                    
                except Exception as e:
                    results.append({
                        'customer_id': customer_data.get('customer_id'),
                        'error': str(e)
                    })
            
            # Log batch prediction
            org_service._log_audit_event(
                org.id, 'batch_prediction_made', 'prediction', None,
                user_id=user.id, user_email=user.email,
                event_data={'batch_size': len(customers), 'results_count': len(results)}
            )
            
            return jsonify({
                'success': True,
                'results': results,
                'batch_size': len(customers),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Batch prediction error: {e}")
            return jsonify({'error': 'Batch prediction failed'}), 500
    
    # ==================== CUSTOMER MANAGEMENT ====================
    
    @app.route('/api/v2/customers', methods=['GET'])
    @require_auth
    @require_permission('customer.read')
    def list_customers():
        """List customers for organization"""
        try:
            org = g.current_organization
            
            # Parse query parameters
            page = int(request.args.get('page', 1))
            per_page = min(int(request.args.get('per_page', 50)), 100)
            
            filters = {}
            if request.args.get('risk_level'):
                filters['churn_risk_level'] = request.args.get('risk_level')
            if request.args.get('status'):
                filters['status'] = request.args.get('status')
            
            # Get customers with organization context
            customers = org_service.get_organization_customers(
                org_id=org.id,
                limit=per_page,
                offset=(page - 1) * per_page,
                filters=filters
            )
            
            return jsonify({
                'customers': [customer.to_dict() for customer in customers],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': len(customers)  # In production, get actual count
                }
            })
            
        except Exception as e:
            logger.error(f"Customer listing error: {e}")
            return jsonify({'error': 'Failed to list customers'}), 500
    
    @app.route('/api/v2/customers', methods=['POST'])
    @require_auth
    @require_permission('customer.create')
    def create_customer():
        """Create new customer"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Customer data required'}), 400
            
            user = g.current_user
            org = g.current_organization
            
            # Add created_by and organization context
            customer_data = {**data, 'created_by': user.id}
            
            customer = org_service.create_customer(org.id, customer_data)
            
            return jsonify({
                'success': True,
                'message': 'Customer created successfully',
                'customer': customer.to_dict()
            }), 201
            
        except Exception as e:
            logger.error(f"Customer creation error: {e}")
            return jsonify({'error': 'Failed to create customer'}), 500
    
    @app.route('/api/v2/customers/<customer_id>', methods=['GET'])
    @require_auth
    @require_permission('customer.read')
    def get_customer(customer_id):
        """Get customer details"""
        try:
            org = g.current_organization
            
            customer = get_customer_by_id(org.id, customer_id)
            if not customer:
                return jsonify({'error': 'Customer not found'}), 404
            
            # Get prediction history
            prediction_history = get_customer_prediction_history(org.id, customer_id)
            
            return jsonify({
                'customer': customer.to_dict(),
                'prediction_history': prediction_history
            })
            
        except Exception as e:
            logger.error(f"Customer retrieval error: {e}")
            return jsonify({'error': 'Failed to get customer'}), 500
    
    # ==================== API KEY ENDPOINTS ====================
    
    @app.route('/api/v2/predict/api', methods=['POST'])
    @require_api_key
    def api_predict():
        """API key-based prediction endpoint"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            org_id = g.current_organization_id
            
            pred_request = PredictionRequest(
                customer_id=data.get('customer_id', 'api'),
                features=data.get('features', {}),
                organization_id=org_id
            )
            
            result = prediction_service.predict(pred_request)
            
            return jsonify({
                'prediction': result.prediction,
                'probability': result.probability,
                'model': result.model_name,
                'timestamp': result.timestamp.isoformat()
            })
            
        except Exception as e:
            logger.error(f"API prediction error: {e}")
            return jsonify({'error': 'Prediction failed'}), 500
    
    # ==================== MODEL MANAGEMENT ====================
    
    @app.route('/api/v2/models', methods=['GET'])
    @require_auth
    @require_permission('analytics.read')
    def list_models():
        """List available models"""
        try:
            models = registry.list_models()
            return jsonify({
                'models': [
                    {
                        'id': model_id,
                        'metadata': metadata,
                        'versions': registry.get_model_versions(model_id)
                    }
                    for model_id, metadata in models.items()
                ]
            })
            
        except Exception as e:
            logger.error(f"Model listing error: {e}")
            return jsonify({'error': 'Failed to list models'}), 500
    
    @app.route('/api/v2/models/<model_id>/performance', methods=['GET'])
    @require_auth
    @require_permission('analytics.read')
    def get_model_performance(model_id):
        """Get model performance metrics"""
        try:
            org = g.current_organization
            
            # Get performance metrics (filtered by organization in production)
            performance_data = monitor.get_model_performance(model_id)
            
            return jsonify({
                'model_id': model_id,
                'performance': performance_data
            })
            
        except Exception as e:
            logger.error(f"Model performance error: {e}")
            return jsonify({'error': 'Failed to get model performance'}), 500
    
    # ==================== A/B TESTING ====================
    
    @app.route('/api/v2/ab-tests', methods=['GET'])
    @require_auth
    @require_permission('analytics.read')
    def list_ab_tests():
        """List A/B tests"""
        try:
            tests = ab_testing.list_tests()
            return jsonify({'tests': tests})
            
        except Exception as e:
            logger.error(f"A/B test listing error: {e}")
            return jsonify({'error': 'Failed to list A/B tests'}), 500
    
    @app.route('/api/v2/ab-tests', methods=['POST'])
    @require_auth
    @require_permission('analytics.read')  # Should be admin permission in production
    def create_ab_test():
        """Create new A/B test"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Test configuration required'}), 400
            
            test_id = ab_testing.create_test(
                name=data['name'],
                model_a=data['model_a'],
                model_b=data['model_b'],
                traffic_split=data.get('traffic_split', 0.5),
                description=data.get('description', '')
            )
            
            return jsonify({
                'success': True,
                'test_id': test_id,
                'message': 'A/B test created successfully'
            })
            
        except Exception as e:
            logger.error(f"A/B test creation error: {e}")
            return jsonify({'error': 'Failed to create A/B test'}), 500
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def get_customer_by_id(org_id: str, customer_id: str):
        """Get customer by ID within organization context"""
        if not db_connection:
            return None
        
        with org_service.organization_context(org_id):
            with db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, external_id, email, first_name, last_name, company,
                           churn_probability, churn_risk_level, status, created_at
                    FROM customers 
                    WHERE (id = %s OR external_id = %s) AND organization_id = %s
                """, (customer_id, customer_id, org_id))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                from enterprise.models import Customer
                return Customer(
                    id=row[0], external_id=row[1], email=row[2],
                    first_name=row[3], last_name=row[4], company=row[5],
                    churn_probability=row[6], churn_risk_level=ChurnRiskLevel(row[7]) if row[7] else None,
                    status=CustomerStatus(row[8]), created_at=row[9]
                )
    
    def store_prediction_result(org_id: str, customer_id: str, result, user_id: str):
        """Store prediction result in database"""
        if not db_connection:
            return
        
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO prediction_history 
                    (organization_id, customer_id, model_name, model_version, 
                     prediction_value, confidence_score, features_used, 
                     predicted_by, ab_test_id, model_variant)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    org_id, customer_id, result.model_name, result.model_version,
                    result.probability, result.confidence, 
                    json.dumps(result.features_used), user_id,
                    result.ab_test_id, result.model_variant
                ))
                
                # Update customer's latest prediction
                cursor.execute("""
                    UPDATE customers 
                    SET churn_probability = %s, 
                        churn_risk_level = %s, 
                        last_prediction_at = %s,
                        prediction_model = %s
                    WHERE id = %s AND organization_id = %s
                """, (
                    result.probability,
                    'high' if result.probability > 0.7 else 'medium' if result.probability > 0.3 else 'low',
                    datetime.now(), result.model_name, customer_id, org_id
                ))
                
                db_connection.commit()
                
        except Exception as e:
            logger.error(f"Failed to store prediction result: {e}")
            db_connection.rollback()
    
    def get_customer_prediction_history(org_id: str, customer_id: str, limit: int = 50):
        """Get customer's prediction history"""
        if not db_connection:
            return []
        
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT model_name, model_version, prediction_value, 
                           confidence_score, predicted_at, ab_test_id
                    FROM prediction_history 
                    WHERE organization_id = %s AND customer_id = %s
                    ORDER BY predicted_at DESC
                    LIMIT %s
                """, (org_id, customer_id, limit))
                
                history = []
                for row in cursor.fetchall():
                    history.append({
                        'model_name': row[0],
                        'model_version': row[1],
                        'prediction': row[2],
                        'confidence': row[3],
                        'predicted_at': row[4].isoformat(),
                        'ab_test_id': row[5]
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Failed to get prediction history: {e}")
            return []
    
    return app

def load_legacy_models(registry: ModelRegistry):
    """Load existing pickle models into the new registry"""
    import pickle
    import os
    
    legacy_models = {
        'XGBoost': 'xgb_model.pkl',
        'KNeighbors': 'knn_model.pkl', 
        'GBoosting': 'gb_model.pkl',
        'RandomForest': 'rf_model.pkl',
        'SVM': 'svm_model.pkl',
        'LogisticRegression': 'lr_model.pkl',
        'NeuralNetwork': 'nn_model.pkl'
    }
    
    for model_name, filename in legacy_models.items():
        if os.path.exists(filename):
            try:
                with open(filename, 'rb') as f:
                    model = pickle.load(f)
                
                # Mock feature data for registration
                mock_features = {
                    'CreditScore': 650, 'Age': 35, 'Tenure': 5, 'Balance': 50000,
                    'NumOfProducts': 2, 'HasCrCard': 1, 'IsActiveMember': 1,
                    'EstimatedSalary': 75000, 'Geography_France': 0, 
                    'Geography_Germany': 1, 'Geography_Spain': 0,
                    'Gender_Male': 1, 'Gender_Female': 0
                }
                
                X_test = pd.DataFrame([mock_features])
                y_test = [0]  # Mock target
                
                registry.register_model(
                    model=model,
                    model_id=model_name,
                    algorithm=model_name,
                    X_test=X_test,
                    y_test=y_test,
                    features=list(mock_features.keys()),
                    hyperparameters={}
                )
                
                logger.info(f"Loaded legacy model: {model_name}")
                
            except Exception as e:
                logger.warning(f"Failed to load legacy model {model_name}: {e}")

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)

import json
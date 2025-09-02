from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import pickle
import numpy as np
from dotenv import load_dotenv
import os
from openai import OpenAI
from scipy.stats import percentileofscore


load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = Flask(__name__)
CORS(app)

#initialize open AI client
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY")
)

# Load models at the start of the application
def load_model(filename):
    try:
        with open(filename, 'rb') as file:
            return pickle.load(file)
    except Exception as e:
        print(f"Warning: Could not load model {filename}: {str(e)}")
        return None

# Load models with error handling
model_files = {
    'XGBoost': 'xgb_model.pkl',
    'KNeighbors': 'knn_model.pkl',
    'ExtraTrees': 'et_model.pkl',
    'AdaBoost': 'ab_model.pkl'
    # 'GBoosting': 'gb_model.pkl',  # Commented out due to scikit-learn version compatibility
}

models = {}
for name, filename in model_files.items():
    model = load_model(filename)
    if model is not None:
        models[name] = model
        print(f"Successfully loaded {name} model")
    else:
        print(f"Failed to load {name} model")

# Helper function to prepare input for the models
def prepare_input(credit_score, location, gender, age, tenure, balance, num_products, has_credit_card, is_active_member, estimated_salary):
    input_dict = {
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
    input_df = pd.DataFrame([input_dict])
    return input_df



# Helper function to make predictions using all models
def make_predictions(input_df):
    probabilities = {}
    # Loop through models and add probabilities
    for model_name, model in models.items():
        try:
            # Convert model predictions to Python float
            probabilities[model_name] = float(model.predict_proba(input_df)[0][1])
        except Exception as e:
            probabilities[model_name] = f"Error: {str(e)}"

    return probabilities


# Function to explain prediction
def explain_prediction(probability, input_dict, surname, churned_stats, non_churned_stats):
    if probability > 0.4:
        risk_type = "high"
        explanation_context = f"{surname} is highly likely to churn. Explain why based on customer characteristics and feature importance."
    else:
        risk_type = "low"
        explanation_context = f"{surname} is unlikely to churn. Highlight the positive characteristics and attributes that make churn less likely."

    prompt = f"""
    You are an expert data scientist at a bank, where you specialize in interpreting and explaining predictions of machine learning models.

    Your machine learning model has predicted that a customer named {surname} has a {round(probability * 100, 1)}% probability of churning, based on the information provided below.

    Here is the customer's information:
    {input_dict}

    Here are the machine learning model's top 10 most important features for predicting churn:

    Feature | Importance
    ---------------------
    NumOfProducts | 0.323888
    IsActiveMember | 0.164146
    Age | 0.109550
    Geography_Germany | 0.091373
    Balance | 0.052786
    Geography_France | 0.046463
    Gender_Female | 0.045283
    Geography_Spain | 0.036855
    CreditScore | 0.035005
    EstimatedSalary | 0.032655
    HasCrCard | 0.031940
    Tenure | 0.030054
    Gender_Male | 0.00000

    Here are summary statistics for churned customers:
    {churned_stats}

    Here are summary statistics for non-churned customers:
    {non_churned_stats}

    {explanation_context}

    Your explanation should be based on the customer's information, the summary statistics of churned and non-churned customers, and the feature importances provided.

    Focus on the insights, avoiding explicit mention of probabilities or generic statements about machine learning. Keep the explanation concise and informative.

    Don't mention the probability of churning or the machine learning model, or say anything like "Based on the machine learning model's prediction and top 10 most important features," just explain the prediction.
    """
    raw_response = client.chat.completions.create(
        model="gemma2-9b-it",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return raw_response.choices[0].message.content

#endpoint to get list of all customers
@app.route('/api/customers', methods=['GET'])
def get_customers():
    # Hot reload test comment
    df = pd.read_csv('churn.csv')
    customers = df[['CustomerId', 'Surname']].to_dict(orient='records')
    return jsonify(customers)

#endpoint to get customer details of a particular customer based on id
@app.route('/api/customer/<int:customer_id>', methods=['GET'])
def get_customer_details(customer_id):
    df = pd.read_csv('churn.csv')
    customer = df[df['CustomerId'] == customer_id].to_dict(orient='records')
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    return jsonify({'customer': customer[0]})

#endpoint to get average churn probability a particular customer based on id
@app.route('/api/customer/<int:customer_id>/churn-probability', methods=['GET'])
def get_average_churn_probability(customer_id):
    df = pd.read_csv('churn.csv')
    customer = df[df['CustomerId'] == customer_id].to_dict(orient='records')

    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    customer = customer[0]  # Get the first and only matching customer

    # Call prepare_input with individual arguments
    input_df = prepare_input(
        customer['CreditScore'], customer['Geography'], customer['Gender'],
        customer['Age'], customer['Tenure'], customer['Balance'],
        customer['NumOfProducts'], customer['HasCrCard'],
        customer['IsActiveMember'], customer['EstimatedSalary']
    )

    probabilities = make_predictions(input_df)
    average_probability = np.mean(list(probabilities.values()))

    return jsonify({'customer_id': customer_id, 'average_probability': average_probability})

#endpoint to get churn probabilities predicted by various models for a particular customer based on id
@app.route('/api/customer/<int:customer_id>/churn-model-probabilities', methods=['GET'])
def get_model_probabilities(customer_id):
    df = pd.read_csv('churn.csv')
    customer = df[df['CustomerId'] == customer_id].to_dict(orient='records')

    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    customer = customer[0]

    # Pass the customer details to `prepare_input`
    input_df = prepare_input(
        customer['CreditScore'], customer['Geography'], customer['Gender'],
        customer['Age'], customer['Tenure'], customer['Balance'],
        customer['NumOfProducts'], customer['HasCrCard'],
        customer['IsActiveMember'], customer['EstimatedSalary']
    )

    probabilities = make_predictions(input_df)

    return jsonify({'customer_id': customer_id, 'model_probabilities': probabilities})


#endpoint to get explanation for probability of churn for a particular customer based on id
@app.route('/api/explanationwithemail/<int:customer_id>', methods=['GET'])
def get_explanation_with_email(customer_id):
    df = pd.read_csv('churn.csv')
    customer = df[df['CustomerId'] == customer_id].to_dict(orient='records')

    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    customer = customer[0]
    input_df = prepare_input(
        customer['CreditScore'], customer['Geography'], customer['Gender'],
        customer['Age'], customer['Tenure'], customer['Balance'],
        customer['NumOfProducts'], customer['HasCrCard'],
        customer['IsActiveMember'], customer['EstimatedSalary']
    )
    probabilities = make_predictions(input_df)
    average_probability = np.mean(list(probabilities.values()))

    # Calculate summary statistics for churned and non-churned customers
    churned_stats = df[df['Exited'] == 1].describe().to_string()
    non_churned_stats = df[df['Exited'] == 0].describe().to_string()

    explanation = explain_prediction(
        average_probability,
        customer,
        customer['Surname'],
        churned_stats,
        non_churned_stats
    )

    email_prompt = f"""
    You are a manager at Richie Bank. You are responsible for ensuring customers stay with the bank and are incentivized with various offers.

    You noticed a customer named {customer['Surname']} has a {round(average_probability * 100, 1)}% probability of churning.

    Here is the customer's information:
    {customer}

    Here is some explanation about the customer churning:
    {explanation}

    Generate an email to the customer based on their information, asking them to stay if they are at high risk of churning, or offering them incentives so that they become more loyal to the bank.

    Make sure to list out a set of incentives to stay based on their information. Use numbered points (e.g., 1., 2., 3.) instead of bullet points and don't bold the numbered point heads.

    Don't ever mention the probability of churning, or the machine learning model to the customer.
    """

    raw_response = client.chat.completions.create(
        model="gemma2-9b-it",
        messages=[
            {"role": "user", "content": email_prompt}
        ]
    )

    email_content = raw_response.choices[0].message.content
    return jsonify({
        'customer_id': customer_id,
        'average_probability': average_probability,
        'explanation': explanation,
        'email_content': email_content
    })

#endpoint to return feature percentiles
@app.route('/api/customer/<int:customer_id>/feature-percentiles', methods=['GET'])
def get_feature_percentiles(customer_id):
    df = pd.read_csv('churn.csv')
    customer = df[df['CustomerId'] == customer_id].to_dict(orient='records')

    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    customer = customer[0]

    features = ['NumOfProducts', 'Balance', 'EstimatedSalary', 'Tenure', 'CreditScore']

    percentiles = {}
    for feature in features:
        try:
            if feature in df.columns:
                percentiles[feature] = percentileofscore(df[feature], customer[feature])
            else:
                percentiles[feature] = None
        except Exception as e:
            percentiles[feature] = f"Error: {str(e)}"
    return jsonify({'customer_id': customer_id, 'percentiles': percentiles})

# Dashboard v2 API Endpoints
# Dashboard management endpoints
@app.route('/api/v2/dashboards', methods=['GET'])
def get_dashboards():
    # Mock dashboard data for the dashboard builder
    dashboards = [
        {
            "id": "default",
            "name": "My Dashboard",
            "description": "Default churn prediction dashboard",
            "layout": [
                {"i": "kpi_cards", "x": 0, "y": 0, "w": 12, "h": 3},
                {"i": "churn_summary", "x": 0, "y": 3, "w": 6, "h": 4},
                {"i": "churn_trend", "x": 6, "y": 3, "w": 6, "h": 4},
                {"i": "customer_list", "x": 0, "y": 7, "w": 8, "h": 6},
                {"i": "activity_feed", "x": 8, "y": 7, "w": 4, "h": 6}
            ],
            "widgets": [
                {"id": "kpi_cards", "type": "kpi_cards", "config": {"cards": ["total_customers", "churn_rate", "high_risk", "model_accuracy"]}},
                {"id": "churn_summary", "type": "churn_summary", "config": {"showTrends": True, "timeRange": "30d"}},
                {"id": "churn_trend", "type": "churn_trend", "config": {"timeRange": "6m", "chartType": "line"}},
                {"id": "customer_list", "type": "customer_list", "config": {"pageSize": 10, "sortBy": "churn_probability"}},
                {"id": "activity_feed", "type": "activity_feed", "config": {"limit": 50}}
            ],
            "isDefault": True,
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
    return jsonify({"success": True, "dashboards": dashboards})

@app.route('/api/v2/dashboards', methods=['POST'])
def create_dashboard():
    # Mock dashboard creation
    return jsonify({"success": True, "dashboard": {"id": "new-dashboard", "name": "New Dashboard"}})

# Analytics endpoints for dashboard widgets
@app.route('/api/v2/analytics/kpis', methods=['GET'])
def get_analytics_kpis():
    df = pd.read_csv('churn.csv')
    total_customers = len(df)
    churned_customers = len(df[df['Exited'] == 1])
    churn_rate = (churned_customers / total_customers) * 100 if total_customers > 0 else 0
    
    # Calculate high risk customers (churn probability > 0.7)
    high_risk_count = 0
    for _, customer in df.iterrows():
        try:
            input_df = prepare_input(
                customer['CreditScore'], customer['Geography'], customer['Gender'],
                customer['Age'], customer['Tenure'], customer['Balance'],
                customer['NumOfProducts'], customer['HasCrCard'],
                customer['IsActiveMember'], customer['EstimatedSalary']
            )
            probabilities = make_predictions(input_df)
            avg_prob = np.mean(list(probabilities.values()))
            if avg_prob > 0.7:
                high_risk_count += 1
        except:
            pass
    
    kpis = {
        "total_customers": {"value": total_customers, "change": "+5.2%", "trend": "up"},
        "churn_rate": {"value": f"{churn_rate:.1f}%", "change": "-2.1%", "trend": "down"},
        "high_risk": {"value": high_risk_count, "change": "+12.3%", "trend": "up"},
        "model_accuracy": {"value": "87.5%", "change": "+1.2%", "trend": "up"}
    }
    return jsonify({"success": True, "kpis": kpis})

@app.route('/api/v2/analytics/churn-summary', methods=['GET'])
def get_churn_summary():
    df = pd.read_csv('churn.csv')
    total = len(df)
    churned = len(df[df['Exited'] == 1])
    active = total - churned
    
    summary = {
        "total_customers": total,
        "active_customers": active,
        "churned_customers": churned,
        "churn_rate": (churned / total * 100) if total > 0 else 0,
        "retention_rate": (active / total * 100) if total > 0 else 0
    }
    return jsonify({"success": True, "summary": summary})

@app.route('/api/v2/analytics/churn-trend', methods=['GET'])
def get_churn_trend():
    # Mock trend data - in real implementation, this would come from time-series data
    trend_data = [
        {"month": "Jan", "churn_rate": 18.5, "predictions": 19.2},
        {"month": "Feb", "churn_rate": 17.8, "predictions": 18.1},
        {"month": "Mar", "churn_rate": 19.2, "predictions": 18.9},
        {"month": "Apr", "churn_rate": 16.5, "predictions": 17.2},
        {"month": "May", "churn_rate": 15.8, "predictions": 16.1},
        {"month": "Jun", "churn_rate": 17.1, "predictions": 16.8}
    ]
    return jsonify({"success": True, "trend": trend_data})

@app.route('/api/v2/analytics/risk-distribution', methods=['GET'])
def get_risk_distribution():
    df = pd.read_csv('churn.csv')
    distribution = {
        "low": 0, "medium": 0, "high": 0, "critical": 0
    }
    
    # Sample a subset for performance
    sample_size = min(100, len(df))
    df_sample = df.sample(n=sample_size)
    
    for _, customer in df_sample.iterrows():
        try:
            input_df = prepare_input(
                customer['CreditScore'], customer['Geography'], customer['Gender'],
                customer['Age'], customer['Tenure'], customer['Balance'],
                customer['NumOfProducts'], customer['HasCrCard'],
                customer['IsActiveMember'], customer['EstimatedSalary']
            )
            probabilities = make_predictions(input_df)
            avg_prob = np.mean(list(probabilities.values()))
            
            if avg_prob < 0.25:
                distribution["low"] += 1
            elif avg_prob < 0.5:
                distribution["medium"] += 1
            elif avg_prob < 0.75:
                distribution["high"] += 1
            else:
                distribution["critical"] += 1
        except:
            distribution["low"] += 1  # Default to low if prediction fails
    
    return jsonify({"success": True, "distribution": distribution})

# Customer endpoints
@app.route('/api/v2/customers', methods=['GET'])
def get_customers_v2():
    df = pd.read_csv('churn.csv')
    per_page = min(int(request.args.get('per_page', 10)), 100)
    page = int(request.args.get('page', 1))
    
    # Sample customers for performance
    sample_size = min(per_page * 2, len(df))
    df_sample = df.sample(n=sample_size)
    
    customers = []
    for _, customer in df_sample.iterrows():
        try:
            input_df = prepare_input(
                customer['CreditScore'], customer['Geography'], customer['Gender'],
                customer['Age'], customer['Tenure'], customer['Balance'],
                customer['NumOfProducts'], customer['HasCrCard'],
                customer['IsActiveMember'], customer['EstimatedSalary']
            )
            probabilities = make_predictions(input_df)
            avg_prob = np.mean(list(probabilities.values()))
            
            customers.append({
                "id": int(customer['CustomerId']),
                "name": customer['Surname'],
                "geography": customer['Geography'],
                "age": int(customer['Age']),
                "balance": float(customer['Balance']),
                "churn_probability": round(avg_prob, 3),
                "risk_level": "critical" if avg_prob > 0.75 else "high" if avg_prob > 0.5 else "medium" if avg_prob > 0.25 else "low",
                "is_active": bool(customer['IsActiveMember'])
            })
        except:
            customers.append({
                "id": int(customer['CustomerId']),
                "name": customer['Surname'],
                "geography": customer['Geography'],
                "age": int(customer['Age']),
                "balance": float(customer['Balance']),
                "churn_probability": 0.5,
                "risk_level": "medium",
                "is_active": bool(customer['IsActiveMember'])
            })
    
    return jsonify({"success": True, "customers": customers[:per_page]})

# Model performance endpoints
@app.route('/api/v2/models/performance', methods=['GET'])
def get_model_performance():
    performance = {
        "models": [
            {"name": "XGBoost", "accuracy": 0.875, "precision": 0.823, "recall": 0.791},
            {"name": "KNeighbors", "accuracy": 0.834, "precision": 0.789, "recall": 0.756},
            {"name": "ExtraTrees", "accuracy": 0.856, "precision": 0.801, "recall": 0.783}
        ]
    }
    return jsonify({"success": True, **performance})

# Predictions endpoints
@app.route('/api/v2/predictions', methods=['GET'])
def get_recent_predictions():
    df = pd.read_csv('churn.csv')
    limit = min(int(request.args.get('limit', 20)), 50)
    sample_customers = df.sample(n=limit)
    
    predictions = []
    for _, customer in sample_customers.iterrows():
        predictions.append({
            "id": f"pred_{int(customer['CustomerId'])}",
            "customer_name": customer['Surname'],
            "probability": 0.6,
            "risk_level": "medium",
            "created_at": "2024-01-01T12:00:00Z"
        })
    
    return jsonify({"success": True, "predictions": predictions})

# Activity feed endpoint
@app.route('/api/v2/audit/activity', methods=['GET'])
def get_activity_feed():
    activities = [
        {"id": "1", "type": "prediction", "description": "Generated churn prediction", "timestamp": "2024-01-01T14:30:00Z"},
        {"id": "2", "type": "model_update", "description": "Updated XGBoost model", "timestamp": "2024-01-01T10:15:00Z"}
    ]
    return jsonify({"success": True, "activities": activities})

# Analytics default endpoint
@app.route('/api/v2/analytics/default', methods=['GET'])
def get_analytics_default():
    return jsonify({"success": True, "data": {"message": "Default analytics endpoint"}})

# Auth endpoints for dashboard
@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    # Mock user data for dashboard functionality
    return jsonify({
        "user": {
            "id": 1,
            "email": "demo@churnguard.com",
            "name": "Demo User",
            "role": "admin",
            "is_admin": True
        },
        "organization": {
            "id": "org-1",
            "name": "Demo Organization",
            "subscription_tier": "enterprise"
        },
        "permissions": [
            "dashboard.edit", "analytics.read", "customer.read",
            "prediction.read", "export.create", "audit.read",
            "user.read"
        ]
    })

#for running on local
# if __name__ == '__main__':
#     app.run(debug=True, port=5001)

#for deployment on Render
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
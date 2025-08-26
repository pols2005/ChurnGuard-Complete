from flask import Flask, jsonify
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
    with open(filename, 'rb') as file:
        return pickle.load(file)

models = {
    'XGBoost': load_model('xgb_model.pkl'),
    # 'DecisionTree': load_model('dt_model.pkl'),
    # 'RandomForest': load_model('rf_model.pkl'),
    # 'GaussianNB': load_model('nb_model.pkl'),
    'KNeighbors': load_model('knn_model.pkl'),
    # 'SVC': load_model('svm_model.pkl'),
    'GBoosting': load_model('gb_model.pkl'),
    # 'LogisticReg': load_model('lr_model.pkl'),
    'ExtraTrees': load_model('et_model.pkl'),
    'AdaBoost': load_model('ab_model.pkl')
}

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













#for running on local
# if __name__ == '__main__':
#     app.run(debug=True, port=5001)

#for deplyment on Render
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))


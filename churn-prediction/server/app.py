from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import pickle
import numpy as np
from dotenv import load_dotenv
import os
from openai import OpenAI

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
    else:
        risk_type = "low"
    prompt = f"""
    You are a data scientist at a bank, where you specialize in interpreting and explaining predictions of machine learning models.

    If {surname} has over a 40% risk of churning, i.e. probability of {surname} to churn > 0.4, then generate a 10-sentence explanation and analysis of why {surname} is at risk of churning.

    If {surname} has less than a 40% risk of churning, i.e. probability of {surname} to churn < 0.4, generate a 10-sentence explanation and analysis of why {surname} might not be at risk of churning.

    Use the pronoun to refer to {surname} based on {surname}'s gender in the customer's information.

    A machine learning model has predicted that a customer named {surname} has a {round(probability * 100, 1)}% probability of churning (risk_type ={risk_type}), based on the information provided below.

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
    HasCrCard |	0.031940
    Tenure |	0.030054
    Gender_Male	| 0.000000

    Here are summary statistics for churned customers:
    {churned_stats}

    Here are summary statistics for non-churned customers:
    {non_churned_stats}

    Don't mention the machine learning model, or say anything like "Based on the machine learning model's prediction and top 10 most important features," just explain the prediction. Dont say anything like "based on the information provided or based on the prediction". Don't mention the percentage of churning explicitly - just use words like low or high risk based on risk_type given.

    Do not invent probabilities or statistics that aren't in the input data.

    Do not explicitly mention the 40% probability threshold in the explanation. Also explanation should be in a simple language, that even a non expert in the filed can understand.
    """
    print("EXPLANATION PROMPT", prompt)
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
@app.route('/api/llama/explanation/<int:customer_id>', methods=['GET'])
def get_explanation(customer_id):
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

    return jsonify({
        'customer_id': customer_id,
        'average_probability': average_probability,
        'explanation': explanation
    })
















if __name__ == '__main__':
    app.run(debug=True, port=5001)

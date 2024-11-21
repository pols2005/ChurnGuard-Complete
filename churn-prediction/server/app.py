from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import pickle
import numpy as np

app = Flask(__name__)
CORS(app)

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

@app.route('/api/customers', methods=['GET'])
def get_customers():
    df = pd.read_csv('churn.csv')
    customers = df[['CustomerId', 'Surname']].to_dict(orient='records')
    return jsonify(customers)

@app.route('/api/customer/<int:customer_id>', methods=['GET'])
def get_customer_details(customer_id):
    df = pd.read_csv('churn.csv')
    customer = df[df['CustomerId'] == customer_id].to_dict(orient='records')
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    return jsonify({'customer': customer[0]})

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

if __name__ == '__main__':
    app.run(debug=True, port=5001)

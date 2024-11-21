from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

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


if __name__ == '__main__':
  app.run(debug = True, port=5001)

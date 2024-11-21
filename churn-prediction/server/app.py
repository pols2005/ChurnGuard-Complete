from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route('/api/data', methods=['GET'])
def get_data():
    df = pd.read_csv('churn.csv')
    return df.to_json(orient='records')


if __name__ == '__main__':
  app.run(debug = True, port=5001)

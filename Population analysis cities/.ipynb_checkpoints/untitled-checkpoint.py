from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

# Load dataset
df = pd.read_csv("indian_cities.csv")  # CSV file ka path

@app.route('/most_populous_states', methods=['GET'])
def most_populous_states():
    state_pop = df.groupby("State")["Population"].sum().sort_values(ascending=False).head(10)
    return jsonify(state_pop.to_dict())

if __name__ == '__main__':
    app.run(debug=True)

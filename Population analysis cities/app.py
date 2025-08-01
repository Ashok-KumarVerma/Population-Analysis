from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import os

app = Flask(__name__)
CORS(app)

# -------------------------------
# 1) Load Dataset Once, Globally
# -------------------------------
DATASET_PATH = "dataset.csv"
if not os.path.exists(DATASET_PATH):
    raise FileNotFoundError("Dataset file not found: 'dataset.csv'")

df = pd.read_csv(DATASET_PATH)
df.columns = df.columns.str.strip()
df["state_name"] = df["state_name"].str.strip().str.upper()

# For literacy analysis (filter columns)
literacy_columns = [
    'name_of_city', 'state_name', 'population_total',
    'effective_literacy_rate_total', 'effective_literacy_rate_male',
    'effective_literacy_rate_female'
]
df_literacy = df[literacy_columns].dropna()

print("Available Columns:", df.columns)  # Debugging info

# ------------------------------------
# 2) Routes for Different Functionalities
# ------------------------------------

# ---- A) Main Page for Literacy Analysis
@app.route('/')
def literacy_rate():
    # Renders a template like "literacy_rate.html"
    return render_template('literacy_rate.html')

# ---- B) Analyze Literacy (Histogram)
@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Creates a histogram of the state's literacy rates 
    and returns it as base64-encoded PNG.
    """
    try:
        data = request.json
        state_name = data.get('state_name', '').strip().upper()
        if not state_name:
            return jsonify({'error': "State name is required"}), 400

        # Filter the dataset for the given state
        df_state = df_literacy[df_literacy['state_name'].str.contains(state_name, case=False, na=False)]
        if df_state.empty:
            return jsonify({'error': f"No data available for {state_name}"}), 404

        # Plot: Literacy Rate Distribution
        plt.figure(figsize=(10, 5))
        sns.histplot(df_state['effective_literacy_rate_total'], bins=30, kde=True)
        plt.xlabel("Total Literacy Rate (%)")
        plt.ylabel("Frequency")
        plt.title(f"Literacy Rate Distribution in {state_name}")

        # Convert the figure to base64
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        graph_url = base64.b64encode(img.getvalue()).decode()
        plt.close()

        return jsonify({
            'graph': f"data:image/png;base64,{graph_url}",
            'state': state_name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---- C) Compare Two States (Population, Literacy, etc.)
def generate_comparison_graph(state1, state2, df):
    """
    Compare two states on:
      - population_total
      - effective_literacy_rate_total
      - sex_ratio
      - total_graduates
    """
    statewise_data = df.groupby("state_name").agg({
        "population_total": "sum",
        "effective_literacy_rate_total": "mean",
        "sex_ratio": "mean",
        "total_graduates": "sum"
    }).reset_index()

    selected_states = statewise_data[statewise_data["state_name"].isin([state1, state2])]
    if selected_states.empty or len(selected_states) < 2:
        return None

    states = selected_states["state_name"].values
    metrics = ["Population", "Literacy Rate", "Sex Ratio", "Total Graduates"]
    values = [
        selected_states["population_total"].values,
        selected_states["effective_literacy_rate_total"].values,
        selected_states["sex_ratio"].values,
        selected_states["total_graduates"].values
    ]

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    palettes = ["viridis", "coolwarm", "magma", "cubehelix"]

    for i, ax in enumerate(axes.flat):
        sns.barplot(x=states, y=values[i], ax=ax, palette=palettes[i])
        ax.set_title(f"{metrics[i]} Comparison")
        ax.set_ylabel(metrics[i])

    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    return f"data:image/png;base64,{graph_url}"


@app.route('/compare_states', methods=['POST'])
def compare_states():
    """
    Compare two states on various metrics 
    (population, literacy, etc.)
    """
    try:
        data = request.json
        state1 = data.get("state1", "").strip().upper()
        state2 = data.get("state2", "").strip().upper()

        if not state1 or not state2:
            return jsonify({"error": "Both states must be provided"}), 400

        valid_states = set(df["state_name"].unique())
        if state1 not in valid_states or state2 not in valid_states:
            return jsonify({"error": "Invalid state names"}), 400

        graph_url = generate_comparison_graph(state1, state2, df)
        if graph_url is None:
            return jsonify({"error": "Insufficient data"}), 404

        return jsonify({"graph": graph_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---- D) Top States (e.g. Unemployment Rate)
@app.route('/top_states', methods=['GET'])
def top_states():
    """
    Example route to show top states by 
    'Estimated Unemployment Rate (%)'.
    """
    try:
        if "Estimated Unemployment Rate (%)" not in df.columns:
            return jsonify({"error": "Estimated Unemployment Rate (%) column not found"}), 400

        top_states = (
            df.groupby("state_name")["Estimated Unemployment Rate (%)"]
            .mean().sort_values(ascending=False)
            .head(10)
        )
        return jsonify(top_states.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---- E) Analyze a Single State's Unemployment
@app.route('/analyze_state', methods=['POST'])
def analyze_state():
    """
    Example route for analyzing unemployment data 
    (Estimated Employed, Region, etc.)
    """
    try:
        data = request.json
        state_name = data.get("state_name", "").strip().upper()

        if not state_name:
            return jsonify({"error": "State name is required"}), 400

        df_state = df[df["state_name"] == state_name]
        if df_state.empty:
            return jsonify({"error": "No data available for the entered state."}), 404

        # Example: Sort by 'Estimated Unemployment Rate (%)'
        # then plot a bar chart of 'Estimated Employed' by Region
        if "Estimated Unemployment Rate (%)" not in df.columns or "Region" not in df.columns:
            return jsonify({"error": "Required columns not found"}), 400

        df_sorted = df_state.sort_values(by="Estimated Unemployment Rate (%)", ascending=False).head(10)
        if "Estimated Employed" not in df.columns:
            return jsonify({"error": "No 'Estimated Employed' column found"}), 400

        img = io.BytesIO()
        plt.figure(figsize=(10,5))
        sns.barplot(x="Region", y="Estimated Employed", data=df_sorted, color="blue", alpha=0.7)
        plt.xlabel("Region")
        plt.ylabel("Estimated Employed")
        plt.title(f"Employment in {state_name}")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(img, format='png')
        img.seek(0)
        graph_url = base64.b64encode(img.getvalue()).decode()
        plt.close()

        return jsonify({"graph": f"data:image/png;base64,{graph_url}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---- F) Another Example Route for 4-plot Employment Analysis
@app.route('/analyze_employment', methods=['POST'])
def analyze_employment():
    """
    4-subplot route for region-based analysis:
      - line chart (Year vs Employed)
      - histogram (Employed distribution)
      - box plot (Employed variability)
      - scatter plot (Employed changes by index)
    """
    try:
        data = request.json
        region_name = data.get("region_name", "").strip()
        if not region_name:
            return jsonify({"error": "Please provide a region name"}), 400

        if "Region" not in df.columns:
            return jsonify({"error": "⚠ 'Region' column not found in the dataset!"}), 400

        state_data = df[df["Region"].str.lower() == region_name.lower()]
        if state_data.empty:
            return jsonify({
                "error": f"⚠ No data found for: {region_name}. Available regions: {df['Region'].unique().tolist()}"
            }), 404

        # Find the 'Estimated Employed' column
        estimated_employed_col = None
        for col in df.columns:
            if "employed" in col.lower():
                estimated_employed_col = col
                break
        if not estimated_employed_col:
            return jsonify({"error": "⚠ No column found related to 'Estimated Employed'."}), 400

        sns.set_style("darkgrid")
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # 1) line chart (Year vs Employed)
        if "Year" in state_data.columns:
            sns.lineplot(
                x="Year",
                y=estimated_employed_col,
                data=state_data,
                marker="o",
                ax=axes[0, 0]
            )
            axes[0, 0].set_title(f"Employment Trends in {region_name}")
            axes[0, 0].set_xlabel("Year")
            axes[0, 0].set_ylabel("Estimated Employed")
        else:
            axes[0, 0].set_visible(False)

        # 2) histogram
        sns.histplot(
            state_data[estimated_employed_col],
            bins=10, kde=True, ax=axes[0, 1]
        )
        axes[0, 1].set_title(f"Employment Distribution in {region_name}")
        axes[0, 1].set_xlabel("Estimated Employed")
        axes[0, 1].set_ylabel("Frequency")

        # 3) box plot
        sns.boxplot(y=state_data[estimated_employed_col], ax=axes[1, 0])
        axes[1, 0].set_title(f"Employment Variability in {region_name}")
        axes[1, 0].set_ylabel("Estimated Employed")

        # 4) scatter plot
        sns.scatterplot(
            x=state_data.index,
            y=state_data[estimated_employed_col],
            data=state_data,
            ax=axes[1, 1],
            color="red"
        )
        axes[1, 1].set_title(f"Employment Changes in {region_name}")
        axes[1, 1].set_xlabel("Index")
        axes[1, 1].set_ylabel("Estimated Employed")

        plt.tight_layout()

        # Convert the figure to base64
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        graph_b64 = base64.b64encode(img.getvalue()).decode()
        plt.close()

        return jsonify({
            "message": "Success",
            "region": region_name,
            "graph": f"data:image/png;base64,{graph_b64}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------
# Finally, run the app
# -------------------------------
if __name__ == '__main__':
    app.run(debug=True)


from flask import Flask, render_template, jsonify
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

# Database setup
DATABASE = 'database.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            message TEXT NOT NULL
                          )''')
        conn.commit()

# Load dataset
csv_path = "synth-data.csv"  # Ensure the CSV is in the same directory as this script
df = pd.read_csv(csv_path)
df["DATE"] = pd.to_datetime(df["DATE"])  # Convert date column

# Create the 'static' folder 
if not os.path.exists("static"):
    os.makedirs("static")

# Function to generate visualizations
def generate_visualizations():
    # Visualization 1: Transaction Value Distribution
    plt.figure(figsize=(10, 5))
    plt.hist(df["Transaction Value"], bins=50, edgecolor="black")
    plt.xlabel("Transaction Value")
    plt.ylabel("Frequency")
    plt.title("Distribution of Transaction Values")
    plt.grid(True)
    plt.savefig("static/transaction_distribution.png")
    plt.close()

    # Visualization 2: Total Emissions by Category
    category_emissions = df.groupby("Main Category")["Emission"].sum().sort_values()
    plt.figure(figsize=(12, 6))
    category_emissions.plot(kind="barh")
    plt.xlabel("Total Emissions")
    plt.ylabel("Main Category")
    plt.title("Total Emissions by Category")
    plt.grid(axis="x")
    plt.savefig("static/emissions_by_category.png")
    plt.close()

    # Visualization 3: Emission Trends Over Time
    df_time_series = df.groupby("DATE")["Emission"].sum()
    plt.figure(figsize=(12, 6))
    plt.plot(df_time_series.index, df_time_series.values, marker='o', linestyle='-')
    plt.xlabel("Date")
    plt.ylabel("Total Emission")
    plt.title("Emission Trends Over Time")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.savefig("static/emission_trends.png")
    plt.close()

    # Visualization 4: Cost vs. Transaction Value Scatter Plot
    plt.figure(figsize=(10, 6))
    plt.scatter(df["Transaction Value"], df["COST"], alpha=0.5)
    plt.xlabel("Transaction Value")
    plt.ylabel("Cost")
    plt.title("Cost vs. Transaction Value")
    plt.grid(True)
    plt.savefig("static/cost_vs_transaction.png")
    plt.close()

    # Visualization 5: Highest Emissions by Source and Destination
    if {'SOURCE', 'DESTINATION', 'Emission'}.issubset(df.columns):
        top_emissions = df.groupby(['SOURCE', 'DESTINATION'])['Emission'].sum().nlargest(10).reset_index()
        plt.figure(figsize=(12, 6))
        plt.barh(top_emissions['SOURCE'] + " -> " + top_emissions['DESTINATION'], top_emissions['Emission'])
        plt.xlabel("Emissions")
        plt.ylabel("Source -> Destination")
        plt.title("Top 10 Emissions by Source and Destination")
        plt.grid(axis="x")
        plt.savefig("static/top_emissions.png")
        plt.close()
    else:
        print("Columns 'SOURCE', 'DESTINATION', or 'Emission' not found in the dataset. Skipping this visualization.")

    # Visualization 6: Emissions by Department
    if 'DEPARTMENT' in df.columns:
        department_emissions = df.groupby('DEPARTMENT')['Emission'].sum().sort_values(ascending=False)
        plt.figure(figsize=(12, 6))
        department_emissions.plot(kind="barh")
        plt.xlabel("Total Emissions")
        plt.ylabel("Department")
        plt.title("Emissions by Department")
        plt.grid(axis="x")
        plt.savefig("static/emissions_by_department.png")
        plt.close()

# Generate visualizations at startup
generate_visualizations()

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/messages', methods=['GET', 'POST'])
def messages():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        if request.method == 'POST':
            new_message = request.json.get('message', '')
            cursor.execute('INSERT INTO messages (message) VALUES (?)', (new_message,))
            conn.commit()
            return jsonify({'status': 'success', 'message': 'Message stored!'}), 201
        else:
            cursor.execute('SELECT * FROM messages')
            rows = cursor.fetchall()
            return jsonify(rows)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import joblib
import numpy as np

# --- Configuration ---
DATASET_PATH = 'grocery_store_dataset.csv'
MODEL_OUTPUT_PATH = 'demand_forecast_model.joblib'
TARGET_PRODUCT = 'Banana'  # Replace with a product you want to forecast (e.g., 'Banana')
SALES_COLUMN = 'Price'  # Replace with the actual column representing sales or a proxy
DATE_COLUMN = 'Date'      # Replace with a date column if you have one
N_PREVIOUS_SALES = 1    # Number of previous sales to use for prediction

# --- Load Dataset ---
try:
    df = pd.read_csv(DATASET_PATH)
except FileNotFoundError:
    print(f"Error: Dataset not found at {DATASET_PATH}")
    exit()

# --- Data Preparation (Adapt this section based on your data) ---

if TARGET_PRODUCT not in df['Product'].unique():
    print(f"Error: Product '{TARGET_PRODUCT}' not found in the dataset.")
    exit()

product_df = df[df['Product'] == TARGET_PRODUCT]  # Removed the sort_values() call

if SALES_COLUMN not in product_df.columns:
    print(f"Error: Sales column '{SALES_COLUMN}' not found for '{TARGET_PRODUCT}'.")
    exit()

sales_history = product_df[SALES_COLUMN].values

if len(sales_history) < N_PREVIOUS_SALES + 1:
    print(f"Not enough sales history for '{TARGET_PRODUCT}' to train a model.")
    exit()

# Create features (using the last N sales to predict the next)
X = []
y = []
for i in range(N_PREVIOUS_SALES, len(sales_history)):
    X.append(sales_history[i - N_PREVIOUS_SALES:i])
    y.append(sales_history[i])

X = np.array(X)
y = np.array(y)

# --- Model Training ---
model = LinearRegression()
model.fit(X, y)

# --- Save the Trained Model ---
joblib.dump(model, MODEL_OUTPUT_PATH)
print(f"Demand forecasting model trained and saved to {MODEL_OUTPUT_PATH} for '{TARGET_PRODUCT}'.")
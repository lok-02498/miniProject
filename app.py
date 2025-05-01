from flask import Flask, render_template, send_file, jsonify, request, make_response, redirect, url_for, session
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from decimal import Decimal
import uuid
import traceback
import numpy as np
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A2
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from flask_bcrypt import Bcrypt
import os
import requests
import json
import cv2
import numpy as np
import base64
import io
import datetime
import joblib

app = Flask(__name__)
app.secret_key = os.urandom(24) #Very important for session management
bcrypt = Bcrypt(app)
reader = None # Barcode reader functionality removed

# --- User Data (For demonstration, use a database in production) ---
users = {}

# --- Function to add UUIDs to CSV (Run ONCE to update your CSV) ---
def add_uuid_to_csv(csv_filepath):
    try:
        df = pd.read_csv(csv_filepath)
        if 'id' not in df.columns:   # Check if 'id' column already exists
            df['id'] = [str(uuid.uuid4()) for _ in range(len(df))]
            df.to_csv(csv_filepath, index=False)
            print(f"Added 'id' column to {csv_filepath}")
        else:
            print(f"'id' column already exists in {csv_filepath}")
    except FileNotFoundError:
        print(f"Error: File not found at {csv_filepath}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Call this function ONCE to add 'id' to your CSV:
add_uuid_to_csv('grocery_store_dataset.csv')   # Run this line ONCE

# --- End of UUID adding function ---

@app.route('/download-dataset')
def download_dataset():
    return send_file('grocery_store_dataset.csv', as_attachment=True)

@app.route('/sales')
def sales():
    return render_template('sales.html')

@app.route('/get-inventory')
def get_inventory():
    try:
        df = pd.read_csv('grocery_store_dataset.csv')
        # Correct NaN values in 'Category'
        df['Category'] = df['Category'].apply(lambda x: "N/A" if pd.isna(x) else x)
        # Correct NaN values in 'Expiration Date'
        df['Expiration Date'] = df['Expiration Date'].apply(lambda x: None if pd.isna(x) else x)

        return jsonify(df.to_dict(orient='records'))
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return jsonify({"status": "error", "message": "Dataset file not found"}), 404
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return jsonify({"status": "error", "message": "Error reading dataset", "error": str(e)}), 500

@app.route('/save-inventory', methods=['POST'])
def save_inventory():
    try:
        data = request.get_json()
        # ... (Validation logic remains the same)

        new_item = data
        new_item['id'] = str(uuid.uuid4())

        new_item_df = pd.DataFrame([new_item])
        existing_df = pd.read_csv('grocery_store_dataset.csv')
        updated_df = pd.concat([existing_df, new_item_df], ignore_index=True)

        updated_df.to_csv('grocery_store_dataset.csv', index=False)
        return jsonify({"status": "success", "message": "Inventory updated successfully", "item": new_item}), 201

    except (FileNotFoundError, pd.errors.EmptyDataError):
        return jsonify({"status": "error", "message": "Dataset file not found"}), 404
    except Exception as e:
        print(f"Error saving inventory: {e}")
        return jsonify({"status": "error", "message": "Failed to update inventory", "error": str(e)}), 500

@app.route('/update-inventory', methods=['PUT'])
def update_inventory():
    try:
        data = request.get_json()
        required_fields = ["Product", "Category", "Price", "Stock", "Supplier", "id"]
        for field in required_fields:
            if field not in data or data[field] == "":
                return jsonify({"status": "error", "message": f"Missing or empty field: {field}", "field": field}), 400

        try:
            data['Price'] = Decimal(data['Price'])
            data['Stock'] = int(data['Stock'])
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid Price or Stock value", "field": "price"}), 400

        df = pd.read_csv('grocery_store_dataset.csv')

        index_to_update = df[df['id'] == data['id']].index
        if len(index_to_update) == 0:
            return jsonify({"status": "error", "message": "Product not found for update"}), 404

        index_to_update = index_to_update[0]

        for header in data:
            df.loc[index_to_update, header] = data[header]

        df.to_csv('grocery_store_dataset.csv', index=False)
        return jsonify({"status": "success", "message": "Inventory updated successfully"}), 200

    except (FileNotFoundError, pd.errors.EmptyDataError):
        return jsonify({"status": "error", "message": "Dataset file not found"}), 404
    except KeyError as e:
        trace = traceback.format_exc()
        print(f"KeyError in update_inventory: {e}")
        print(trace)
        return jsonify({"status": "error", "message": f"Missing or invalid key: {e}", "trace": trace}), 400

    except Exception as e:
        trace = traceback.format_exc()
        print(f"Error updating inventory: {e}")
        print(trace)
        return jsonify({"status": "error", "message": "Failed to update inventory", "error": str(e), "trace": trace}), 500

@app.route('/delete-inventory/<item_id>', methods=['DELETE'])
def delete_inventory(item_id):
    try:
        df = pd.read_csv('grocery_store_dataset.csv')
        df = df[df['id'] != item_id]
        df.to_csv('grocery_store_dataset.csv', index=False)
        return jsonify({"status": "success", "message": "Item deleted successfully"}), 200
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return jsonify({"status": "error", "message": "Dataset file not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/reports/inventory_pdf')
def inventory_report_pdf():
    try:
        df = pd.read_csv('grocery_store_dataset.csv')
        pdf_io = BytesIO()
        doc = SimpleDocTemplate(pdf_io, pagesize=A2, orientation='landscape') #set orientation
        data = [df.columns.tolist()] + df.values.tolist()

        # 1. Calculate maximum column widths
        max_widths = [0] * len(df.columns)
        for row in data:
            for i, cell in enumerate(row):
                cell_text = str(cell)   # Convert to string to handle numbers, dates
                max_widths[i] = max(max_widths[i], len(cell_text))

        # 2. Convert character lengths to points (adjust multiplier as needed)
        col_widths = [width * 7 for width in max_widths]   #   Adjust the 7 to change size.

        table = Table(data, colWidths=col_widths)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),     #   set font size
        ])
        table.setStyle(style)
        elements = [table]
        doc.build(elements)
        pdf_io.seek(0)
        response = make_response(pdf_io.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=inventory_report.pdf'
        return response
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error generating PDF report: {e}"}), 500


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users[username] = hashed_password
        return redirect(url_for('index')) # Redirect to your main page after signup
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)
        if user and bcrypt.check_password_hash(user, password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return "Login failed"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))


@app.route('/visualizations')
def visualizations():
    try:
        df = pd.read_csv('grocery_store_dataset.csv')

        # 1. Category Distribution (Bar Chart)
        plt.figure(figsize=(10, 6))
        sns.barplot(x=df['Category'].value_counts().index, y=df['Category'].value_counts().values)
        plt.title('Distribution of Items by Category')
        plt.xlabel('Category')
        plt.ylabel('Number of Items')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        img1_io = io.BytesIO()
        plt.savefig(img1_io, format='png')
        img1_io.seek(0)
        img1_base64 = base64.b64encode(img1_io.read()).decode('utf-8')
        plt.close()

        # 2. Price Distribution (Histogram)
        plt.figure(figsize=(10, 6))
        sns.histplot(df['Price'], bins=20, kde=True)
        plt.title('Distribution of Item Prices')
        plt.xlabel('Price')
        plt.ylabel('Frequency')
        plt.tight_layout()
        img2_io = io.BytesIO()
        plt.savefig(img2_io, format='png')
        img2_io.seek(0)
        img2_base64 = base64.b64encode(img2_io.read()).decode('utf-8')
        plt.close()

        # 3. Stock Levels (Scatter Plot)
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=df.index, y=df['Stock'])
        plt.title('Inventory Stock Levels')
        plt.xlabel('Item Index')
        plt.ylabel('Stock Level')
        plt.tight_layout()
        img3_io = io.BytesIO()
        plt.savefig(img3_io, format='png')
        img3_io.seek(0)
        img3_base64 = base64.b64encode(img3_io.read()).decode('utf-8')
        plt.close()

        # 4. Price vs. Stock (Scatter Plot)
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x='Price', y='Stock', data=df)
        plt.title('Price vs. Stock Level')
        plt.xlabel('Price')
        plt.ylabel('Stock Level')
        plt.tight_layout()
        img4_io = io.BytesIO()
        plt.savefig(img4_io, format='png')
        img4_io.seek(0)
        img4_base64 = base64.b64encode(img4_io.read()).decode('utf-8')
        plt.close()

        return render_template('visualizations.html',
                                   img1=img1_base64,
                                   img2=img2_base64,
                                   img3=img3_base64,
                                   img4=img4_base64)

    except FileNotFoundError:
        return "Error: grocery_store_dataset.csv not found."
    except Exception as e:
        return f"An error occurred during visualization generation: {e}"
try:
    demand_model = joblib.load('demand_forecast_model.joblib')
except FileNotFoundError:
    demand_model = None
    print("Warning: demand_forecast_model.joblib not found.")
# --- Configuration ---
MODEL_PATH = 'demand_forecast_model.joblib'
N_PREVIOUS_SALES = 5   # Define N_PREVIOUS_SALES here

try:
    demand_model = joblib.load(MODEL_PATH)
except FileNotFoundError:
    demand_model = None
    print("Warning: demand_forecast_model.joblib not found.")

@app.route('/predict_demand', methods=['POST'])
def predict_demand():
    if not demand_model:
        return jsonify({"error": "Demand forecasting model not loaded."}), 500

    data = request.get_json()
    product_name = data.get('product_name')
    historical_data = data.get('historical_data') # Example: list of historical sales

    if not product_name or not historical_data:
        return jsonify({"error": "Missing product_name or historical_data."}), 400

    # Prepare data for prediction
    try:
        if len(historical_data) < N_PREVIOUS_SALES:
            return jsonify({"error": f"Not enough historical data provided. Need at least {N_PREVIOUS_SALES} data points."}), 400

        # Take the last N_PREVIOUS_SALES values as features
        last_sales = historical_data[-N_PREVIOUS_SALES:]
        features = np.array(last_sales).reshape(1, -1) # Reshape to (1, num_features) for a single prediction

        prediction = demand_model.predict(features)[0] # Predict and get the single prediction
        return jsonify({"product_name": product_name, "predicted_demand": round(prediction, 2)})
    except Exception as e:
        return jsonify({"error": f"Error during prediction: {str(e)}"}), 500

LOW_STOCK_THRESHOLD = 10
EXPIRING_SOON_DAYS = 7

def get_low_stock_items():
    try:
        df = pd.read_csv('grocery_store_dataset.csv')
        low_stock = df[df['Stock'] <= LOW_STOCK_THRESHOLD].to_dict(orient='records')
        return low_stock
    except FileNotFoundError:
        return []

def get_expiring_soon_items():
    try:
        df = pd.read_csv('grocery_store_dataset.csv')
        today = datetime.datetime.now().date()
        expiring_items = []
        for index, row in df.iterrows():
            expiration_date_str = row['Expiration Date']
            if pd.notna(expiration_date_str):
                try:
                    expiry_date = datetime.datetime.strptime(expiration_date_str, '%Y-%m-%d').date() # Corrected
                    if (expiry_date - today).days <= EXPIRING_SOON_DAYS and (expiry_date - today).days >= 0:
                        expiring_items.append(row.to_dict())
                except ValueError:
                    try:
                        expiry_date = datetime.datetime.strptime(expiration_date_str, '%m/%d/%Y').date() # Corrected
                        if (expiry_date - today).days <= EXPIRING_SOON_DAYS and (expiry_date - today).days >= 0:
                            expiring_items.append(row.to_dict())
                    except ValueError:
                        try:
                            expiry_date = datetime.datetime.strptime(expiration_date_str, '%d/%m/%Y').date() # Corrected
                            if (expiry_date - today).days <= EXPIRING_SOON_DAYS and (expiry_date - today).days >= 0:
                                expiring_items.append(row.to_dict())
                        except ValueError:
                            print(f"Warning: Could not parse expiration date: {expiration_date_str} for product: {row['Product']}")
        return expiring_items
    except FileNotFoundError:
        return []
@app.route('/dashboard')
def dashboard():
    low_stock_notifications = get_low_stock_items()
    expiring_soon_notifications = get_expiring_soon_items()
    notifications = {
        'low_stock': low_stock_notifications,
        'expiring_soon': expiring_soon_notifications
    }
    return render_template('dashboard.html', notifications=notifications)

@app.route('/notifications')
def notifications_endpoint():
    low_stock_notifications = get_low_stock_items()
    expiring_soon_notifications = get_expiring_soon_items()
    notifications = {
        'low_stock': low_stock_notifications,
        'expiring_soon': expiring_soon_notifications
    }
    return jsonify(notifications)

if __name__ == '__main__':
    app.run(debug=True)
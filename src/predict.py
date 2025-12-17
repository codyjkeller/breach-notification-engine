import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# 1. Load Data
try:
    df = pd.read_csv('data/fines.csv')
    print(f"📊 Historical Data Loaded: {len(df)} records (2015-2025)")
except FileNotFoundError:
    print("❌ Error: 'data/fines.csv' not found.")
    exit()

# 2. Train Model (X = Records + Revenue, y = Fine)
X = df[['records_exposed', 'revenue_millions']]
y = df['fine_amount']

model = LinearRegression()
model.fit(X, y)

def predict_fine(records, revenue):
    # The model predicts the fine based on inputs
    prediction = model.predict([[records, revenue]])
    
    # Logic: Fines can't be negative (Linear Regression artifact)
    estimated_fine = max(0, prediction[0])
    
    return estimated_fine

if __name__ == "__main__":
    print("-" * 40)
    print("🔮 REGULATORY FINE PREDICTOR (v2.0)")
    print("-" * 40)
    
    # Interactive Input
    try:
        in_records = int(input("Enter Records Exposed (e.g. 50000): "))
        in_revenue = int(input("Enter Company Revenue (Millions): "))
        
        est_fine = predict_fine(in_records, in_revenue)
        
        print(f"\n🏢 SCENARIO ANALYZED:")
        print(f"   • Records Lost: {in_records:,}")
        print(f"   • Annual Revenue: ${in_revenue:,}M")
        print(f"\n💸 ESTIMATED LIABILITY: ${est_fine:,.2f}")
        
    except ValueError:
        print("❌ Invalid input. Please enter numbers only.")

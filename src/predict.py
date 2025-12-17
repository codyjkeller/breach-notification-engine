import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

# 1. Load Data
df = pd.read_csv('data/fines.csv')
print("📊 Historical Data Loaded:")
print(df.head())

# 2. Prepare Features (X) and Target (y)
# We use 'records_exposed' and 'revenue' to predict 'fine_amount'
X = df[['records_exposed', 'revenue_millions']]
y = df['fine_amount']

# 3. Train Model
model = LinearRegression()
model.fit(X, y)

# 4. Predict Function
def predict_fine(records, revenue):
    prediction = model.predict([[records, revenue]])
    return f"${prediction[0]:,.2f}"

if __name__ == "__main__":
    # Scenario: 75,000 records exposed, Company Revenue $200M
    est_fine = predict_fine(75000, 200)
    print(f"\n🔮 PREDICTION:")
    print(f"Estimated Regulatory Fine: {est_fine}")

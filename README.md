# 📉 Regulatory Fine Predictor

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Scikit-Learn](https://img.shields.io/badge/ML-Linear%20Regression-orange)
![Data](https://img.shields.io/badge/Data-2015--2025-green)

**Data-Driven Risk Intelligence.**
This tool utilizes linear regression modeling on a curated dataset of historical data breaches (2015–2025) to forecast potential regulatory fines. It helps CISOs and Risk Officers quantify financial exposure based on breach magnitude and company revenue.

## 📊 Dataset Overview
The model is trained on `data/fines.csv`, which includes **35 verified enforcement actions** spanning:
* **Regulations:** GDPR, HIPAA, CCPA, SEC, FTC, NYDFS.
* **Sectors:** Tech, Finance, Healthcare, Retail.
* **Timeline:** 2015 (Pre-GDPR) to 2025 (Projected AI Act enforcement).

## 🛠️ Architecture
1.  **Ingestion:** Loads historical fine data (`fines.csv`).
2.  **Training:** Fits a Linear Regression model correlating `records_exposed` and `annual_revenue` to `fine_amount`.
3.  **Prediction:** Interactive CLI allows users to input hypothetical breach scenarios to estimate liability.

## 🚀 Quick Start

### 1. Installation
```bash
pip install pandas scikit-learn numpy

python src/predict.py

🔮 REGULATORY FINE PREDICTOR (v2.0)
----------------------------------------
Enter Records Exposed (e.g. 50000): 75000
Enter Company Revenue (Millions): 200

🏢 SCENARIO ANALYZED:
   • Records Lost: 75,000
   • Annual Revenue: $200M

💸 ESTIMATED LIABILITY: $1,450,200.00

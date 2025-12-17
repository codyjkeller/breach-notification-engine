# 📈 Regulatory Fine Predictor

![Python](https://img.shields.io/badge/Python-Data%20Science-blue)
![Scikit-Learn](https://img.shields.io/badge/ML-Linear%20Regression-orange)

**Data Science for GRC.**
This tool utilizes linear regression on historical enforcement data to forecast potential regulatory fines based on breach magnitude (records exposed) and company size.

## 🛠️ How it Works
1.  **Ingest:** Loads historical fine data (`fines.csv`).
2.  **Train:** Fits a Linear Regression model correlating `records_exposed` and `revenue` to `fine_amount`.
3.  **Predict:** Outputs estimated financial liability for new scenarios.

## 🚀 Quick Start
```bash
pip install -r requirements.txt
python src/predict.py

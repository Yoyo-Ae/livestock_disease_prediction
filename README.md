# Livestock Disease Prediction System
A machine learning-based system for predicting livestock diseaes outbreaks in sub-Saharan Africa using secondary epidemiological, climate and livestock population data

## Stack
- **ML:** Python. Scikit-learn, XGBoost, MLflow
- **API:** FatsAPI, PostgreSQL, Docker
- **Web:** React
- **Farmer Interface:** Africa's talking USSD

## Disease Covered
FMD > PPR > LSD > CBPP > RVF

## Target Region
Nigeria and sub-Saharan Africa

## Setup
1. clone the repo
2. Copy `.env.example` to `.env` and fill in credeentials
3. Run `pip install -r requirement.txt`
4. Run `psql -U postgres -d livestock_db -f db/schema.sql`
5. Run `uvicron api.main:app --reload` to start API
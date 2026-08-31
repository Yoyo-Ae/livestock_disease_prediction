import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
import joblib
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

print("\nPHASE 3: PREPROCESSING\n")

#LOADING DATA FROM FROM POSTGRESQL
print(f"Loading data from PostgreSQL")
df = pd.read_sql("SELECT * FROM outbreak_records", engine)

print(f"data shape: {df.shape}\n")
print(f"columns: {df.columns.tolist()}\n")
print(f"Outbreak rate: {df['outbreak_occurred'].mean():.2%}\n")

#Handle missing values
print(f"Mising values count: {df.isnull().sum()}\n")

num_cols = [
    "livestock_density", "rainfall_mm", "temp_celsuis", "rolling_outbreak_count"
]

#fill numeriacl columns with median values
for col in num_cols:
    if col in df.columns:
        median_val = df[col].median()
        missing_count = df[col].isnull().sum()
        df[col] = df[col].fillna(median_val)
        print(f" {col}: filled {missing_count} missing median {median_val:.2%}\n")

#fill catergorical columns with most common value
cat_cols = ["species", "season"]
for col in cat_cols:
    if col in df.columns:
        model_val = df[col].mode()[0]
        missing_count = df[col].isnull().sum()
        df[col] = df[col].fillna(model_val)
        print(f" {col}: filled {missing_count} with {model_val}")

#Drop rows still missing critical identifier
before = len(df)
df = df.dropna(subset=["country", "disease_type", "year", "month"])
after = len(df)
print(f"Dropped {before - after} rows")

print(f"Missing values after: {df.isnull().sum()}")

#FEATURE ENGINEERING
#rolling_outbreak- done in integrate.py

df = df.sort_values(
    ["country", "disease_type", "year", "month"]
)

#df["rolling_outbreak_count"] = (
#   df.groupby(["country","disease_type"])["outbreak_occurred"].transform(lambda x: x.shift(1).rolling(window=12, min_periods=1).sum())
#    .fillna(0).astype(int))

#print("rolling_outbreak_count sample: ")
#print(df[["country", "disease_type","year","month","outbreak_occurred","rolling_outbreak_count"]].head(20))

#season-done in integrate.py

#def assign_season(month):
# if month in [4,5,6,7,8,9,10]:
#   return "Wet"
# else:
#   return "Dry"
#df["season"] = df["month"].apply(assign_season)
#print("\nSeason distribution:")
#print(df["season"].value_counts())

#climate anomalies
if "rainfall_mm" in df.columns:
    monthly_mean_rain = df.groupby(
        ["country", "month"]
    )["rainfall_mm"].transform("mean")
    df["rainfall_anomaly"] = df["rainfall_mm"] - monthly_mean_rain
    print(f"  Rainfall_anomaly range: "
          f"{df['rainfall_anomaly'].min():.2f} to "
          f"{df['rainfall_anomaly'].max():.2f}\n")

if "temp_celsuis" in df.columns:
    monthly_mean_temp = df.groupby(
        ["country", "month"]
    )["temp_celsuis"].transform("mean")
    df["temp_anomaly"] = df["temp_celsuis"] - monthly_mean_temp
    print(f"  temp_anomaly range: "
          f"{df['temp_anomaly'].min():.2f} to "
          f"{df['temp_anomaly'].max():.2f}\n")

#livestock density
if "livestock_density" in df.columns:
    df["livestock_density_log"] = np.log1p(df["livestock_density"])
    print(f" livestock_density_log: "
          f"{df['livestock_density_log'].min():.2f} to "
          f"{df['livestock_density_log'].max():.2f}\n")
    

#month_sin month_cos- encode months as cyclical features so month 1 and 12 aint so far apart
df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["month"]/ 12)
print("month_sin and month_cos added\n")
print(f"\nDataset shape after feature engineering: {df.shape}\n")

#ENCODE CATERGORICAL VARIABLES
os.makedirs("models", exist_ok=True)

encode_cols = ["country", "disease_type", "species","season"]

encoders = {}

for col in encode_cols:
    if col in df.columns:
        le = LabelEncoder()
        df[f"{col}_encoded"] = le.fit_transform(df[col].astype(str))
        encoders[col] = le
        joblib.dump(le, f"models/le_{col}.pkl")
        print(f" {col}: {df[col].nunique()} unique values encoded\n")
        print(f" Classes: {list(le.classes_[:5])}{'...' if len(le.classes_) > 5 else ''}\n")
print(" Encoders saved to models\n")

#DEFINE FEATURE MATRIX
print(f"columns: {df.columns.tolist()}\n")
ALL_FEATURES =[
    "country_encoded",
    "disease_type_encoded",
    "species_encoded",
    "year",
    "month_sin",
    "month_cos",
    "season_encoded",
    "livestock_density_log",
    "rainfall_mm",
    "temp_anomaly",
    "rainfall_anomaly",
    "temp_celsuis",
    "rolling_outbreak_count"
]

FEATURES = [f for f in ALL_FEATURES if f in df.columns]
TARGET = "outbreak_occurred"

print(f"Features selected: ({len(FEATURES)})")
for f in FEATURES:
    print(f" - {f}")

x = df[FEATURES].copy()
y = df[TARGET].copy()

print(f"X shape: {x.shape}\n Y shape: {y.shape}\n")
print(f"Class distribution: outbreak(1): {y.sum()}({y.mean():.2%})\n and No outbreak(0): {(y==0).sum()}({(y==0).mean():.2%})\n")

if x.isnull().sum().sum() > 0:
    a = x.isnull().sum().sum() > 0
    b = x.isnull().sum()
    x = x.fillna(0)
    print(f"filled {a} and {b} missing values with 0\n")

else:
    print("no missing values in features\n")

#TRAIN TEST SPLIT
x_train, x_test, y_train, y_test = train_test_split(
    x,y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(f"Train Size: {x_train.shape}\n Test size: {x_test.shape}\n Train outbreak rate:{y_train.mean():.2%}\n Test outbreak rate:{y_test.mean():.2%}\n ")

#APPLY SMOTE
smote = SMOTE(random_state=42, k_neighbors = 5)


print(f"SMOTE FAILED: Back to original training dataset\n")
x_train_res, y_train_res = x_train, y_train

#SCALCING FEATURES
scaler = StandardScaler()

x_train_scaled = scaler.fit_transform(x_train_res)

x_test_scaled = scaler.fit_transform(x_test)

joblib.dump(scaler, "models/scaler.pkl")
print(f"Scaler saved to models/scaler.pkl\n x_train_scaled: {x_train_scaled.shape}\n x_test_scaled: {x_test_scaled.shape}\n")

#SAVE SPLITS
import pickle

splits = {
    "x_train": x_train_scaled,
    "x_test": x_test_scaled,
    "y_train": y_train_res,
    "y_test": y_test,
    "x_test_raw": x_test,
    "features_names": FEATURES
}

joblib.dump(splits, "models/splits.pkl")
print("splits saved to models/splits.pkl\n")

df.to_csv("data/processed/preprocessed_dataset.csv", index=False)
print("Preprocessed dataset saved to data/processed\n")

joblib.dump(FEATURES, "models/feature_names.pkl")
print("feature names saved to models/")

print(f"Final training set:{x_train_scaled.shape[0]} rows\nFinal test set: {x_test_scaled.shape[0]}rows\nfeatures used: {len(FEATURES)}")

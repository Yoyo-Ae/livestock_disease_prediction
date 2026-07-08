import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

print("Loading raw datasets....")

# LOAD EMPRES-i
# laod all 5 disease files and combine

empres_files = [
    "data/raw_data/empres_fmd.csv",
    "data/raw_data/empres_ppr.csv",
    "data/raw_data/empres_lsd.csv",
    "data/raw_data/empres_cbpp.csv",
    "data/raw_data/empres_rvf.csv"
]

empres_list = []
for f in empres_files:
    if os.path.exists(f):
        df = pd.read_csv(f, on_bad_lines='skip', skiprows=11)
        empres_list.append(df)
empres = pd.concat(empres_list, ignore_index=True)

empres = empres.rename(columns={
    "Event.ID" : "event_id",
    "Global.ID": "global_id",
    "Disease": "disease_type",
    "Serotype": "serotype",
    "Region":"region",
    "Subregion":"subregion",
    "Country":"country",
    "Admin.level.1":"admin_level",
    "Locality":"locality",
    "Latitude":"latitude",
    "Longitude":"longitude",
    "Diagnosis.source":"diagnosis_source",
    "Diagnosis.status":"diagnosis_status",
    "Animal.type":"animal_affected",
    "Species":"species",
    "Observation.date..dd.mm.yyyy.":"obs_date",
    "Report.date..dd.mm.yyyy.":"report_date",
    "Humans.affected":"humans_affected",
    "Humans.deaths":"humans_deaths"
})

empres["obs_date"] = pd.to_datetime(empres["obs_date"], dayfirst=True, errors="coerce")
empres["year"] = empres["obs_date"].dt.year
empres["month"] = empres["obs_date"].dt.month

SSA_COUNTRIES= [
    "Nigeria", "Niger", "Cameroon", "Chad", "Benin", "Ghana", "Burkina Faso","Mali","Senegal","Guinea","Togo",
    "Cote d' Ivoire", "Sierra Leone", "Gambia", "Kenya", "Ethiopia","Uganda","Tanzania","Somalia","South Sudan","Rwanda",
    "Burundi","Democratic Republic of Congo", "Central African Republic", "Republic of Congo", "Sudan", "South Africa", "Zimbabwe",
    "Zambia", "Mozambique", "Malawi", "Angola","Namibia","Botswana","Madagascar"
]
SSA_DISEASE =[
    "Foot and mouth disease",
    "Peste des petits ruminants",
    "Lumpy skin disease",
    "Contagious bovine pleuropneumonia",
    "Rift Valley fever"

]
SSA_SPECIES =[
    "Cattle", "Bovines","Goats","Sheep","Small ruminants","Camelids","Poultry","Swine","Pigs"
]

empres = empres[empres["country"].isin(SSA_COUNTRIES)]
empres = empres[empres["disease_type"].isin(SSA_DISEASE)]
empres = empres[empres["species"].str.contains(
    "Cattle|Bovine|Goat|Ruminant|Poultry|Sheep",
    case=False, na=False
)]
print(f"species no {empres['species'].value_counts()}\n")

def clean_species(species_str):
    if pd.isna(species_str):
        return "Other"
    s= str(species_str).lower().strip()

    s = s.replace("domestic -", "").replace("wild -", "").replace("captive -", "")

    if "|" in s:
        s=s.split("|")[0].strip()
    if any(word in s for word in [
        "cattle", "bovine","bovines","bos","zebu","cow","bull","calf","buffalo","buffaloe",
        "ruminant","bontebok","springbok","ibex"
    ]):
        return "Cattle"
    if "goat/sheep" in s:
        return "Small Ruminants"
    if any(word in s for word in [
        "goat", "caprine", "capra"
    ]):
        return "Goats"
    if any(word in s for word in [
        "sheep","ovine","ovis", "lamb"
    ]):
        return "Sheep"
    if any(word in s for word in [
        "small ruminant"
    ]):
        return "Small Ruminants"
    if any(word in s for word in [
        "swine", "pig", "poricine", "sus", "boar","sow"
    ]):
        return "Swine"
    if any(word in s for word in[
        "poultry", "chicken", "gailus","birds","fowl","duck","turkey","hen"
    ]):
        return "Poultry"
    if any(word in s for word in[
        "camel", "camelid","camelids","alpaca","llama"
    ]):
        return "Camelids"
    if any(word in s for word in[
        "mammal","unspecified","unidentified"
    ]):
        return "Other"
    return "Other"

empres["species"] = empres["species"].apply(clean_species)
print(f"\nSpecies after cleaning: {empres["species"].value_counts()}\n")


empres = empres.dropna(subset=["country","disease_type","year","month"])
empres["year"] = empres["year"].astype(int)
empres["month"] = empres["month"].astype(int)

print(f"EMPRES-i after filtering: {empres.shape}")
print(empres["country"].value_counts().head(10))
print(empres["disease_type"].value_counts())
print(empres['admin_level'].value_counts())

#LOAD FAOSTAT LIVESTOCK
faostat = pd.read_csv("data/raw_data/faostat_livestock2.csv")

faostat = faostat.rename(columns={
    "Area":"country",
    "Item": "livestock_item",
    "Year": "year",
    "Value": "livestock_population"
})

faostat_agg = faostat.groupby(["country", "year"])["livestock_population"].sum().reset_index()
faostat_agg.columns = ["country","year", "total_livestock"]

print(f"FAOSTAT aggregated: {faostat_agg.shape}")

#LOAD LAND AREA
land = pd.read_csv("data/raw_data/faostat_land_area2.csv")

land = land.rename(columns={
    "Area":"country",
    "Year":"year",
    "Value":"land_area_km2"
})

land_latest = land.groupby("country")["land_area_km2"].mean().reset_index()

print(f"Land area: {land_latest.shape}")

#LOAD CLIMATE

climate = pd.read_csv("data/raw_data/nasa_climate.csv")
print(f"Climate: {climate.shape}")

#CREATE BASE DATASET
empres["outbreak_occurred"] = 1
outbreak = empres.groupby(
    ["country","disease_type","species","year","month"]
).agg(
    outbreak_occurred =("outbreak_occurred", "max")
    ).reset_index()

print(f"Positive outbreak rows: {len(outbreak)}")

countries = outbreak["country"].unique().tolist()
diseases = outbreak["disease_type"].unique().tolist()
years = list(range(2005, 2025))
months = list(range(1,13))

species_map = (
    outbreak.groupby("disease_type")["species"].agg(lambda x: x.value_counts().index[0]).to_dict()
)

print("Species map: ", species_map)
import itertools
grid_rows = []
for country,disease,year,month in itertools.product(
    countries,diseases,years,months
):
    grid_rows.append({
        "country": country,
        "disease_type":disease,
        "species": species_map.get(disease, "Cattle"),
        "year": year,
        "month": month,
        "outbreak_occurred": 0
    })
grid = pd.DataFrame(grid_rows)
print(f"Full grid size: {len(grid)}")

outbreak["_key"] =(
    outbreak["country"] + "|" +
    outbreak["disease_type"] + "|" +
    outbreak["year"].astype(str) + "|" +
    outbreak["month"].astype(str)
)

grid["_key"] =(
    grid["country"] + "|" +
    grid["disease_type"] + "|" +
    grid["year"].astype(str) + "|" +
    grid["month"].astype(str)
)

outbreak_keys = set(outbreak["_key"])
negatives = grid[~grid["_key"].isin(outbreak_keys)].copy()
negatives = negatives.drop(columns=["_key"])

outbreak_clean = outbreak.drop(columns=["_key"])
df= pd.concat([outbreak_clean, negatives], ignore_index=True)
print(f"After concat: ")
print(f"total rows: {len(df)}")
print(f"outb=1: {(df['outbreak_occurred']==1).sum()}")
print(f"outb=0: {(df['outbreak_occurred']==0).sum()}")
print(f"outb rate: {df['outbreak_occurred'].mean():.2%}")

df = df.sample(frac=1, random_state=42).reset_index(drop=True)
#df['geopolitical_zone'] = empres['admin_level']

print(f"\nCombined dataset: {df.shape}")
print(f"Outbreak rate: {df['outbreak_occurred'].mean():.2%}")
print(f"Outbreak rows: {outbreak['outbreak_occurred'].sum()}")
print(f"No-Outbreak: {(df['outbreak_occurred'] == 0).sum()}")
print(f"columns: {df.columns.tolist()}\n")

#MERGE FAOSTAT
df = pd.merge(df,faostat_agg, on=["country","year"], how="left")
df = pd.merge(df, land_latest,on="country", how="left")

#livestock density
df['livestock_density'] = df["total_livestock"] / df["land_area_km2"]

print(f"After FAOSTAT merge: {df.shape}")
print(f"Missing livestock density: {df['livestock_density'].isnull().sum()}")

#MERGE CLIMATE
df = pd.merge(df,climate, on=["country","year","month"], how="left")

print(f"After climate: {df.shape}")
print(f"Missing temp: {df['temp_celsuis'].isnull().sum()}")
print(f"Missing rainfall: {df['rainfall_mm'].isnull().sum()}")
print(f"columns: {df.columns.tolist()}\n")

#ADD GEOPOLITICAL ZONE FOR NIGERIA
NIGERIA_ZONES ={
    "Kano":"North West", "Kaduna":"North West","Sokoto":"North West","Katsina":"North West", "Zamfara":"North West","Kebbi":"North West","Jigawa":"North West",
    "Borno":"North East", "Bauchi":"North East","Gombe":"North East", "Yobe":"North East", "Adamawa":"North East","Taraba":"North East",
    "Plateau":"North Central", "Niger":"North Central", "Kwara":"North Central","Kogi":"North Central","Benue":"North Central","Nasarawa":"North Central","FCT":"North Central",
    "Lagos":"South West","Ogun":"South West", "Oyo":"South West","Osun":"South West","Ondo":"South West","Ekiti":"South West",
    "Enugu":"South East", "Anambra":"South East","Imo":"South East", "Abia":"South East","Ebonyi":"South East",
    "Rivers":"South South", "Delta":"South South","Cross River":"South South","Akwa Ibom":"South South", "Bayelsa":"South South","Edo":"South South"
}
#df["geopolitical_zone"] = df["country"].map(empres['admin_level'])
print(f"columns: {df.columns.tolist()}\n")

#CLEAN UP
#drop rows missing values/critical fields
df= df.dropna(subset=["country", "disease_type","year","month","outbreak_occurred"])

#save processed dataset
df.to_csv("data/processed/integrated_dataset.csv", index=False)
print(f"\nIntegrated dataser saved: {df.shape}")

#postgresql write up
df = df.sort_values(["country", "disease_type", "year", "month"]).reset_index(drop=True)


#preprocess -feature engineering
df["rolling_outbreak_count"] = (
    df.groupby(["country","disease_type"])["outbreak_occurred"].transform(lambda x: x.shift(1).rolling(window=12, min_periods=1).sum())
    .fillna(0).astype(int)
)

print("rolling_outbreak_count sample: ")
print(df[["country", "disease_type","year","month","outbreak_occurred","rolling_outbreak_count"]].head(20))

def assign_season(month):
    if month in [4,5,6,7,8,9,10]:
        return "Wet"
    else:
        return "Dry"
df["season"] = df["month"].apply(assign_season)
print("\nSeason distribution:")
print(df["season"].value_counts())
db_cols=[
    "country","disease_type","species","year","month","livestock_density","rainfall_mm","temp_celsuis","geopolitical_zone","outbreak_occurred","rolling_outbreak_count","season"
]


db_cols = [c for c in db_cols if c in df.columns]
df_db = df[db_cols].copy()

#write to DB
with engine.begin() as connection:
    connection.execute(text("TRUNCATE TABLE outbreak_records;"))

df_db.to_sql(
    "outbreak_records",
    engine,
    if_exists="append",
    index=False,
    method="multi",
    chunksize=500
)
print(f"\nWritten to PostgreSQL: {len(df_db)} rows")

#Verify
with engine.connect() as conn:
    count = conn.execute(text("SELECT COUNT(*) FROM outbreak_records")).scalar()
    print(f"Total rows in outbreak_records: {count}")
    diseases = conn.execute(text(
        "SELECT disease_type, COUNT(*) as n FROM outbreak_records GROUP BY disease_type"
    )).fetchall()
    print("\nRows per disease: ")
    for row in diseases:
        print(f" {row[0]}: {row[1]}")
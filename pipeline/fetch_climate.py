import requests
import pandas as pd
import time
import os

#load country coords
coords = pd.read_csv("data/raw_data/country_coords.csv")

#filter to African countries only
AFRICAN_COUNTRIES = [
    "Nigeria", "Niger", "Cameroon", "Chad", "Benin", "Ghana", "Burkina Faso", "Mali", "Senegal","Guinea","Togo","Cote d' Ivoire", "Sierra Leone", "Gambia",
    "Liberia", "Guinea-Bissau", "Mauritania","Cap Verde", "Kenya","Ethopia", "Uganda", "Tanzania","Somalia", "South Sudan", "Rwanda", "Burundi", "Djibouti",
    "Eritrea", "Democratic Republic of the Congo", "Central African Republic", "Republic of Congo", "Gabon", "Equatorial Guinea", "South Africa", "Zimbabwe",
    "Zambia", "Mozambique", "Malawi", "Angola", "Namibia", "Botswana", "Lesotho", "Swaziland", "Madagascar", "Sudan"
]

coords = coords[coords["COUNTRY"].isin(AFRICAN_COUNTRIES)]
results = []

print(f"Fetching climate data for {len(coords)} countries...")

for _, row in coords.iterrows():
    country = row["COUNTRY"]
    lat = row["latitude"]
    lon = row["longitude"]

    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    params = {
        "parameters" :"T2M,PRECTOTCORR",
        "community" : "AG",
        "longitude" : lon,
        "latitude" : lat,
        "start" : "2005",
        "end" : "2024",
        "format" : "JSON"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        data = response.json()

        temp_data = data["properties"]["parameter"]["T2M"]
        rain_data = data["properties"]["parameter"]["PRECTOTCORR"]

        for key in temp_data:
            #key format is YYYYMM i.e 202609
            year= int(key[:4])
            month = int(key[4:])
            results.append({
                "country" : country,
                "year": year,
                "month": month,
                "temp_celsuis": temp_data[key],
                "rainfall_mm": rain_data[key]
            })

        print(f" DONE: {country}")
        time.sleep(1)
    except Exception as e:
        print(f"Failed: {country} - {e}")
        continue

climate_df = pd.DataFrame(results)
climate_df.to_csv("data/raw_data/nasa_climate.csv", index=False)
print(f"\nClimate data saved. Shape: {climate_df.shape}")
print(climate_df.head())
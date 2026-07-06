
-- CORE TRAINING DATASET
CREATE TABLE IF NOT EXISTS outbreak_records(
    id SERIAL PRIMARY KEY,
    country VARCHAR(100) NOT NULL,
    disease_type VARCHAR(100) NOT NULL,
    species VARCHAR(80) NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    livestock_density FLOAT,
    rainfall_mm FLOAT,
    temp_celsius FLOAT,
    rainfall_anomaly FLOAT,
    temp_anomaly FLOAT,
    rolling_outbreak_count INTEGER NOT NULL,
    season VARCHAR(20),
    geopolitical_zone VARCHAR(50),
    outbreak_occurred INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Prediction audit log

CREATE TABLE IF NOT EXISTS prediction_log(
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    source_interface VARCHAR(20) NOT NULL,
    country_encoded INTEGER NOT NULL,
    disease_encoded INTEGER NOT NULL,
    species_encoded INTEGER NOT NULL,
    livestock_density FLOAT,
    rainfall_anomaly FLOAT,
    temp_anomaly FLOAT,
    rolling_outbreak_count INTEGER,
    season_encoded INTEGER,
    predicted_class INTEGER NOT NULL,
    outbreak_probability FLOAT NOT NULL,
    risk_level VARCHAR(10),
    model_version VARCHAR(100)
);


-- ussd session tracker 
CREATE TABLE IF NOT EXISTS ussd_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    phone_number VARCHAR(80) NOT NULL,
    current_step INTEGER NOT NULL DEFAULT 1,
    branch VARCHAR(10),
    zone_selection VARCHAR(50),
    animal_type VARCHAR(50),
    symptom_reported VARCHAR(100),
    season_reported VARCHAR(50),
    number_affected VARCHAR(30),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_updated TIMESTAMP NOT NULL DEFAULT NOW()

);

--index for performance
CREATE INDEX IF NOT EXISTS idx_outbreak_country ON outbreak_records(country);
CREATE INDEX IF NOT EXISTS idx_outbreak_disease ON outbreak_records(disease_type);
CREATE INDEX IF NOT EXISTS idx_outbreak_year ON outbreak_records(year);
CREATE INDEX IF NOT EXISTS idx_log_timestamp ON prediction_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_log_source ON prediction_log(source_interface);
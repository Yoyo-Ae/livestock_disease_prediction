import joblib
import numpy as np
import json, os, logging
from api.config import settings


logger = logging.getLogger(__name__)

class PredictionService:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.encoders={}
        self.feature_names=[]
        self.metadata={}
        self.threshold = settings.OPTIMAL_THRESHOLD
        self._load_atrefacts()
    
    def _load_atrefacts(self):
        try:
            self.model = joblib.load(settings.MODEL_PATH)
            logger.info(f"Model loaded: {type(self.model).__name__}")

            self.scaler = joblib.load(settings.SCALER_PATH)
            logger.info(f"Scaler loaded")

            self.feature_names = joblib.load(settings.FEATURE_NAME_PATH)
            logger.info(f"Feature: {self.feature_names}")

            encoder_cols = ["country", "disease_type", "species", "season"]
            for col in encoder_cols:
                path = os.path.join(settings.ENCODERS_DIR, f"le_{col}.pkl")
                if os.path.exists(path):
                    self.encoders[col] = joblib.load(path)
                    logger.info(f"Enocder loaded: {col}")
            
            if os.path.exists("models/model_metadata.json"):
                with open("models/model_metadata.json") as f:
                    self.metedata = json.load(f)
                self.threshold = self.metadata.get(
                    "optimal_threshold", settings.OPTIMAL_THRESHOLD
                )
                logger.info(f"Threshold from metadata: {self.threshold}")
            logger.info("All artefacts loaded Successfully")
        
        except Exception as e:
            logger.error(f"Failed to load artefacts successfully:{e}")
            raise
    
    def _safe_encode(self, encoder_key: str, value: str)-> int:
        #Encode a categorical value safely
        #if the values was not seen during training of the model, return 0 instead of crashing program

        if encoder_key not in self.encoders:
            return 0
        le = self.encoders[encoder_key]
        try:
            return int(le.transform([value])[0])
        except ValueError:
            classes = list(le.classes_)
            value_lower = value.lower()
            for cls in classes:
                if value_lower in cls.lower() or cls.lower() in value_lower:
                    return int(le.transform([cls])[0])
            logger.warning(
                f"Unknown {encoder_key} value: '{value}'."
                f"Known values: {list(le.classes_)}. Using 0."
            )
            return 0
    
    def build_feature_vector(self, input_data)-> np.ndarray:
        #converts raw input into the feature vector the model expects, inthe correct order
        import math

        country_enc = self._safe_encode("country", input_data.country)
        disease_enc = self._safe_encode("disease_type", input_data.disease_type)
        species_enc = self._safe_encode("species", input_data.species)
        season_enc = self._safe_encode("season", input_data.season)

        month_sin = math.sin(2*math.pi*input_data.month/12)
        month_cos = math.cos(2*math.pi*input_data.month/12)

        livestock_density_log = math.log1p(input_data.livestock_density)

        rainfall_anomaly = input_data.rainfall_mm - 85.0
        temp_anomaly= input_data.temp_celsuis - 29.5

        feature_map = {
            "country_encoded": country_enc,
            "disease_type_encoded": disease_enc,
            "species_encoded": species_enc,
            "year": input_data.year,
            "month_sin": month_sin,
            "month_cos": month_cos,
            "season_encoded": season_enc,
            "livestock_density_log": livestock_density_log,
            "rainfall_mm": input_data.rainfall_mm,
            "temp_celsuis": input_data.temp_celsuis,
            "rainfall_anomaly": rainfall_anomaly,
            "temp_anomaly": temp_anomaly,
            "rolling_outbreak_count": input_data.rolling_outbreak_count

        }

        vector = np.array([
            feature_map.get(f,0) for f in self.feature_names
        ]).reshape(1,-1)
        
        return vector
    def classify_risk(self, probability: float) -> tuple:
        #Classify the probability into three risk levels: LOW, MODERATE, HIGH
        #Return a tuple of (risk_level, predicted_class, tone)
        #predicted_class is 1 for HIGH risk, 0 for LOW or MODERATE risk
        #tone is a string indicating the tone of the message: "low", "moderate", "high"
        thresholds = self.metadata.get("risk_thresholds", {
            "low_max":      0.10,
            "moderate_max": 0.20,
            "high_min":     0.20
        })

        if probability < thresholds["low_max"]:
            return "LOW", 0, "low"
        elif probability < thresholds["moderate_max"]:
            return "MODERATE", 0, "moderate"
        else:
         return "HIGH", 1, "high"

    def predict(self, input_data) -> dict:
    # Build feature vector
        vector = self.build_feature_vector(input_data)

    # Scale
        vector_scaled = self.scaler.transform(vector)

    # Predict probability
        proba = float(self.model.predict_proba(vector_scaled)[0][1])

    # Classify into three risk levels
        risk_level, predicted_class, tone = self.classify_risk(proba)

    # Build message based on risk level
        disease_short = {
            "foot and mouth disease":           "Foot and Mouth Disease (FMD)",
            "peste des petits ruminants":        "Peste des Petits Ruminants (PPR)",
            "lumpy skin disease":                "Lumpy Skin Disease (LSD)",
            "contagious bovine pleuropneumonia": "CBPP",
            "rift valley fever":                 "Rift Valley Fever (RVF)"
        }.get(input_data.disease_type.lower(), input_data.disease_type)

        if tone == "high":
            message = (
                f"HIGH RISK: {disease_short} outbreak likely in "
                f"{input_data.country}. Isolate sick animals "
                f"immediately and contact your nearest veterinary "
                f"officer. Probability: {proba:.0%}."
            )
        elif tone == "moderate":
            message = (
                f"MODERATE RISK: Conditions in {input_data.country} "
                f"are favourable for {disease_short}. Increase "
                f"monitoring of your livestock and watch for early "
                f"symptoms. Probability: {proba:.0%}."
            )
        else:
            message = (
                f"LOW RISK: No {disease_short} outbreak expected in "
                f"{input_data.country} at this time. Continue "
                f"routine monitoring. Probability: {proba:.0%}."
            )

        return {
            "predicted_class":        predicted_class,
            "outbreak_probability":   round(proba, 4),
            "risk_level":             risk_level,
            "message":                message,
            "threshold_used":         self.metadata.get(
                                    "risk_thresholds",
                                    {"high_min": 0.20}
                                  ),
            "model_name":             type(self.model).__name__,
            "country_encoded":        self._safe_encode("country", input_data.country),
            "disease_encoded":        self._safe_encode("disease_type", input_data.disease_type),
            "species_encoded":        self._safe_encode("species", input_data.species),
            "livestock_density":      input_data.livestock_density,
            "rainfall_anomaly":       input_data.rainfall_mm - 85.0,
            "temp_anomaly":           input_data.temp_celsuis - 29.5,
            "rolling_outbreak_count": input_data.rolling_outbreak_count,
            "season_encoded":         self._safe_encode("season", input_data.season)
        }
prediction_service = PredictionService()

    
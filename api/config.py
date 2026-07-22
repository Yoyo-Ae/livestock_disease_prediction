import os 
from dotenv import load_dotenv

load_dotenv()

class Settings: 
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    OPTIMAL_THRESHOLD: float = 0.20
    MODEL_PATH: str = "models/best_model.pkl"
    SCALER_PATH: str = "models/scaler.pkl"
    FEATURE_NAME_PATH: str = "models/feature_names.pkl"
    ENCODERS_DIR: str = "models"
    ENVIRONMENT: str = os.getenv("ENVIROMENT", "development")
    API_PORT: int = int(os.getenv("API PORT", 8000))

settings = Settings()
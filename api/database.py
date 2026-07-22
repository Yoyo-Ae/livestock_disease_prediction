from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker
from api.config import settings
import logging


logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping = True,
    pool_size = 5,
    max_overflow = 10
)

SessionLocal = sessionmaker(autocommit=False, autoflush = False, bind = engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def log_prediction(
        source_interface: str,
        country_encoded: int,
        disease_encoded: int,
        species_encoded: int,
        livestock_density: float,
        rainfall_anomaly: float,
        temp_anomaly: float,
        rolling_outbreak_count: float,
        season_encoded: int,
        predicted_class: int,
        outbreak_probability: float,
        risk_level: str,
        model_version: str
):
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO prediction_log(
                              source_interface,
                              country_encoded,
                              disease_encoded,
                              species_encoded,
                              livestock_density,
                              rainfall_anomaly,
                              temp_anomaly,
                              rolling_outbreak_count,
                              season_encoded,
                              predicted_class,
                              outbreak_probability,
                              risk_level,
                              model_version
                              ) VALUES (
                                 :source, :ce, :de, :se, :ld,
                                 :ra, :ta, :roc, :season, :pc,
                                 :prob, :risk, :mv
                              )
                              """
            ), {
                "source": source_interface,
                "ce": country_encoded,
                "de": disease_encoded,
                "se": species_encoded,
                "ld": livestock_density,
                "ra": rainfall_anomaly,
                "ta": temp_anomaly,
                "roc": rolling_outbreak_count,
                "season": season_encoded,
                "pc": predicted_class,
                "prob": outbreak_probability,
                "risk": risk_level,
                "mv": model_version
            })
            conn.commit()
    except Exception as e:
        logger.error(f"failed to log prediction {e}")
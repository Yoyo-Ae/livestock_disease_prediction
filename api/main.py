from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import logging, json
from api.models import(
    PredictionInput,
    PredictionOutput,
    HealthResponse,
    PredictionLogEntry
)
from api.predict import prediction_service
from api.database import get_db, log_prediction
from api.config import settings

logging.basicConfig(
    level=logging.INFO,
    format = "%(asctime)s -%(name)s -%(levelname)s-%(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title = "Livestock Disease Prediction API",
    description=(
        "Predicts livestock disease outbreak risk in sub-Saharan Africa "
        "Using a Random Forest model trained on FAO Empres-i, FAOSTAT, "
        "and NASA POWER secondary data"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

#CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#ROUTES
@app.get("/", tags=["Root"])
def root():
    return{
        "message":"Livestock Disease Prediction API",
        "docs": "/docs",
        "health": "/health"
    }
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    return HealthResponse(
        status ="ok",
        model_loaded=prediction_service.model is not None,
        model_name=type(prediction_service.model).__name__,
        threshold=prediction_service.threshold,
        environment=settings.ENVIRONMENT
    )

@app.post("/predict", response_model=PredictionOutput, tags=["Prediction"])
def predict(input_data: PredictionInput):
    try:
        logger.info(
            f"Prediction request: {input_data.country} | "
            f"{input_data.disease_type} | {input_data.species} | "
            f"{input_data.year}-{input_data.month:02d} | "
            f"source={input_data.source}"
        )
        result = prediction_service.predict(input_data)

        log_prediction(
            source_interface=input_data.source,
            country_encoded=result["country_encoded"],
            disease_encoded=result["disease_encoded"],
            species_encoded=result["species_encoded"],
            livestock_density=result["livestock_density"],
            rainfall_anomaly=result["rainfall_anomaly"],
            temp_anomaly=result["temp_anomaly"],
            rolling_outbreak_count=result["rolling_outbreak_count"],
            season_encoded=result["season_encoded"],
            predicted_class=result["predicted_class"],
            outbreak_probability=result["outbreak_probability"],
            risk_level=result["risk_level"],
            model_version=result["model_name"]
        )

        logger.info(
            f"Result: {result['risk_level']} "
            f"(prob={result['outbreak_probability']:.4f})"
        )

        return PredictionOutput(
            predicted_class=result["predicted_class"],
            outbreak_probability=result["outbreak_probability"],
            risk_level=result["risk_level"],
            message=result["message"],
            threshold_used=result["threshold_used"],
            model_name=result["model_name"]
        )
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict_history", tags=["Prediction"])
def get_prediction_history(limit: int=50, db: Session = Depends(get_db)):
    try:
        from sqlalchemy import text
        result = db.execute(text(f"""
                                 SELECT id, timestamp, source_interface, predicted_class,outbreak_probability,risk_level
                                 FROM prediction_log
                                 ORDER BY timestamp DESC
                                 LIMIT :limit
                                 """), {"limit": limit})
        rows = result.fetchall()
        return[
            {
                "id": row[0],
                "timestamp":str(row[1]),
                "source_interface": row[2],
                "predicted_class": row[3],
                "outbreak_probability":row[4],
                "risk_level":row[5]
            }
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/predict/stats", tags=["Prediction"])
def get_prediction_stats():
    try:
        from sqlalchemy import text
        from api.database import engine

        with engine.connect() as conn:
            total = conn.execute(
                text("SELECT COUNT(*) FROM prediction_log")
            ).scalar()
            high_risk = conn.execute(
                text("SELECT COUNT(*) FROM prediction_log WHERE risk_level = 'HIGH'")
            ).scalar()
            by_source = conn.execute(text("""
                                          SELECT source_interface, COUNT(*) as n
                                          FROM prediction_log
                                          GROUP BY source_interface
                                          """)).fetchall()
        return {
            "total_predictions": total,
            "high_risk_count":high_risk,
            "low_risk_count": total - high_risk,
            "high_risk_rate": round(high_risk/total, 4) if total > 0 else 0,
            "by_source": {row[0]: row[1] for row in by_source}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/model/info", tags=["Models"])
def model_info():
    try:
        with open("models/model_metadata.json") as f:
            meta = json.load(f)
        return meta
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/model/features", tags=["Models"])
def feature_info():
    try:
        import pandas as pd
        fi = pd.read_csv("models/feature_importance.csv")
        return fi.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
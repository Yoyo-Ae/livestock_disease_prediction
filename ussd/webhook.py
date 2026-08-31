from fastapi import FastAPI, Form, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import create_engine, text
import requests
import hashlib
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Livestock Disease USSD Webhook")

engine = create_engine(os.getenv("DATABASE_URL"))

PREDICT_URL = os.getenv(
    "PREDICT_URL",
    "http://localhost:8000/predict"  # fallback for local dev
)
#Mapping tables 

COUNTRY_MAP = {
    "1": {"country": "Nigeria",  "rainfall_mm": 95.0,  "temp_celsuis": 29.5, "livestock_density": 32.4},
    "2": {"country": "Kenya",    "rainfall_mm": 85.0,  "temp_celsuis": 25.0, "livestock_density": 28.6},
    "3": {"country": "Ethiopia", "rainfall_mm": 75.0,  "temp_celsuis": 22.0, "livestock_density": 42.1},
    "4": {"country": "Ghana",    "rainfall_mm": 110.0, "temp_celsuis": 28.0, "livestock_density": 18.3},
    "5": {"country": "Uganda",   "rainfall_mm": 130.0, "temp_celsuis": 23.5, "livestock_density": 35.7},
    "6": {"country": "Cameroon", "rainfall_mm": 120.0, "temp_celsuis": 26.5, "livestock_density": 22.8}
}

ANIMAL_MAP = {
    "1": "Cattle",
    "2": "Goats",
    "3": "Sheep",
    "4": "Poultry"
}

SYMPTOM_MAP = {
    "Cattle": {
        "1": {"symptom": "mouth_sores",  "rolling_boost": 3, "disease": "Foot and mouth disease"},
        "2": {"symptom": "skin_lumps",   "rolling_boost": 2, "disease": "Lumpy skin disease"},
        "3": {"symptom": "fever_no_eat", "rolling_boost": 2, "disease": "Contagious bovine pleuropneumonia"},
        "4": {"symptom": "sudden_death", "rolling_boost": 4, "disease": "Rift Valley fever"},
        "5": {"symptom": "none",         "rolling_boost": 0, "disease": "Foot and mouth disease"}
    },
    "Goats": {
        "1": {"symptom": "cough_runny",   "rolling_boost": 3, "disease": "Peste des petits ruminants"},
        "2": {"symptom": "mouth_sores",   "rolling_boost": 2, "disease": "Foot and mouth disease"},
        "3": {"symptom": "sudden_deaths", "rolling_boost": 4, "disease": "Rift Valley fever"},
        "4": {"symptom": "eye_discharge", "rolling_boost": 2, "disease": "Peste des petits ruminants"},
        "5": {"symptom": "none",          "rolling_boost": 0, "disease": "Peste des petits ruminants"}
    },
    "Sheep": {
        "1": {"symptom": "cough_runny",   "rolling_boost": 3, "disease": "Peste des petits ruminants"},
        "2": {"symptom": "mouth_sores",   "rolling_boost": 2, "disease": "Foot and mouth disease"},
        "3": {"symptom": "sudden_deaths", "rolling_boost": 4, "disease": "Rift Valley fever"},
        "4": {"symptom": "eye_discharge", "rolling_boost": 2, "disease": "Peste des petits ruminants"},
        "5": {"symptom": "none",          "rolling_boost": 0, "disease": "Peste des petits ruminants"}
    },
    "Poultry": {
        "1": {"symptom": "sudden_deaths", "rolling_boost": 4, "disease": "Rift Valley fever"},
        "2": {"symptom": "swollen_head",  "rolling_boost": 3, "disease": "Rift Valley fever"},
        "3": {"symptom": "not_moving",    "rolling_boost": 2, "disease": "Rift Valley fever"},
        "4": {"symptom": "twisted_neck",  "rolling_boost": 3, "disease": "Rift Valley fever"},
        "5": {"symptom": "none",          "rolling_boost": 0, "disease": "Rift Valley fever"}
    }
}

#Helpers 

def hash_phone(phone: str) -> str:
    return hashlib.sha256(phone.encode()).hexdigest()

def get_session(session_id: str) -> dict:
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT * FROM ussd_sessions WHERE session_id = :sid"
        ), {"sid": session_id}).fetchone()
        if row:
            return dict(row._mapping)
    return {}

def create_session(session_id: str, phone: str):
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO ussd_sessions
            (session_id, phone_number, current_step)
            VALUES (:sid, :phone, 1)
            ON CONFLICT (session_id) DO NOTHING
        """), {"sid": session_id, "phone": hash_phone(phone)})
        conn.commit()

def update_session(session_id: str, **kwargs):
    if not kwargs:
        return
    set_clause = ", ".join([f"{k} = :{k}" for k in kwargs])
    set_clause += ", last_updated = NOW()"
    with engine.connect() as conn:
        conn.execute(text(
            f"UPDATE ussd_sessions SET {set_clause} "
            f"WHERE session_id = :session_id"
        ), {"session_id": session_id, **kwargs})
        conn.commit()

def call_predict_api(payload: dict) -> dict:
    try:
        response = requests.post(
            PREDICT_URL,
            json=payload,
            timeout=8
        )
        return response.json()
    except Exception as e:
        logger.error(f"Predict API call failed: {e}")
        return None

def format_result(result: dict, animal: str) -> str:
    if not result:
        return (
            "Service temporarily unavailable. "
            "Please try again later."
        )
    risk     = result.get("risk_level", "UNKNOWN")
    prob     = result.get("outbreak_probability", 0)
    prob_pct = int(prob * 100)

    if risk == "HIGH":
        return (
            f"HIGH RISK ({prob_pct}%): Outbreak "
            f"likely in your area. Isolate sick "
            f"{animal.lower()} now. Contact your "
            f"nearest vet officer immediately."
        )
    else:
        return (
            f"LOW RISK ({prob_pct}%): No outbreak "
            f"expected now. Keep observing your "
            f"{animal.lower()}. Check again in 2 weeks."
        )

# USSD Route 

@app.post("/ussd", response_class=PlainTextResponse)
async def ussd_callback(
    sessionId:   str = Form(...),
    phoneNumber: str = Form(...),
    networkCode: str = Form(default=""),
    serviceCode: str = Form(default=""),
    text:        str = Form(default="")
):
    logger.info(
        f"USSD | session={sessionId} | "
        f"phone=...{phoneNumber[-4:]} | text='{text}'"
    )

    parts = [p.strip() for p in text.split("*")] if text else []
    step  = len(parts)

    # ── STEP 0: Welcome ───────────────────────────────────────────
    if step == 0:
        create_session(sessionId, phoneNumber)
        return (
            "CON Welcome to Livestock Alert\n"
            "Select an option:\n"
            "1. Check disease risk\n"
            "2. Report sick animal\n"
            "3. About this service"
        )

    main_choice = parts[0]

    # ── BRANCH C: About ───────────────────────────────────────────
    if main_choice == "3":
        return (
            "END Livestock Disease Alert\n"
            "Covers FMD, PPR, LSD, CBPP & RVF\n"
            "across sub-Saharan Africa.\n"
            "Built by Miva Open University.\n"
            "Dial again anytime. Free to use."
        )

    # ── BRANCH A: Check disease risk ──────────────────────────────
    if main_choice == "1":

        # A-Step 1: Select country
        if step == 1:
            update_session(sessionId, current_step=2, branch="A")
            return (
                "CON Select your country:\n"
                "1. Nigeria\n"
                "2. Kenya\n"
                "3. Ethiopia\n"
                "4. Ghana\n"
                "5. Uganda\n"
                "6. Cameroon"
            )

        country_choice = parts[1] if len(parts) > 1 else ""

        # A-Step 2: Select animal type
        if step == 2:
            if country_choice not in COUNTRY_MAP:
                return (
                    "CON Invalid. Select country:\n"
                    "1. Nigeria\n"
                    "2. Kenya\n"
                    "3. Ethiopia\n"
                    "4. Ghana\n"
                    "5. Uganda\n"
                    "6. Cameroon"
                )
            country_info = COUNTRY_MAP[country_choice]
            update_session(
                sessionId,
                current_step=3,
                zone_selection=country_info["country"]
            )
            return (
                "CON Select animal type:\n"
                "1. Cattle\n"
                "2. Goats\n"
                "3. Sheep\n"
                "4. Poultry"
            )

        animal_choice = parts[2] if len(parts) > 2 else ""

        # A-Step 3: Select symptom
        if step == 3:
            if animal_choice not in ANIMAL_MAP:
                return (
                    "CON Invalid. Select animal:\n"
                    "1. Cattle\n"
                    "2. Goats\n"
                    "3. Sheep\n"
                    "4. Poultry"
                )
            animal = ANIMAL_MAP[animal_choice]
            update_session(
                sessionId,
                current_step=4,
                animal_type=animal
            )

            if animal == "Cattle":
                return (
                    "CON What have you noticed?\n"
                    "1. Sores on mouth or feet\n"
                    "2. Lumps on skin\n"
                    "3. Fever, not eating\n"
                    "4. Sudden deaths\n"
                    "5. No symptoms yet"
                )
            elif animal in ["Goats", "Sheep"]:
                return (
                    "CON What have you noticed?\n"
                    "1. Coughing, runny nose\n"
                    "2. Mouth sores\n"
                    "3. Sudden deaths\n"
                    "4. Eye or nose discharge\n"
                    "5. No symptoms yet"
                )
            else:
                return (
                    "CON What have you noticed?\n"
                    "1. Birds dying suddenly\n"
                    "2. Swollen head or face\n"
                    "3. Birds not moving\n"
                    "4. Twisted necks\n"
                    "5. No symptoms yet"
                )

        symptom_choice = parts[3] if len(parts) > 3 else ""

        # A-Step 4: Run prediction and return result
        if step == 4:
            session      = get_session(sessionId)
            country_name = session.get("state_selection", "Nigeria")
            animal       = session.get("animal_type", "Cattle")

            # Get country climate profile
            country_info = next(
                (v for v in COUNTRY_MAP.values()
                 if v["country"] == country_name),
                COUNTRY_MAP["1"]
            )

            # Get symptom data
            symptom_data = SYMPTOM_MAP.get(animal, {}).get(
                symptom_choice,
                {"symptom": "none", "rolling_boost": 0,
                 "disease": "Foot and mouth disease"}
            )

            update_session(
                sessionId,
                current_step=5,
                symptom_reported=symptom_data["symptom"]
            )

            now    = datetime.now()
            month  = now.month
            season = "Wet" if month in [4,5,6,7,8,9,10] else "Dry"

            payload = {
                "country":                country_info["country"],
                "disease_type":           symptom_data["disease"],
                "species":                animal,
                "year":                   now.year,
                "month":                  month,
                "livestock_density":      country_info["livestock_density"],
                "rainfall_mm":            country_info["rainfall_mm"],
                "temp_celsuis":           country_info["temp_celsuis"],
                "rolling_outbreak_count": symptom_data["rolling_boost"],
                "season":                 season,
                "source":                 "ussd"
            }

            result  = call_predict_api(payload)
            message = format_result(result, animal)

            logger.info(
                f"USSD Result | country={country_name} | "
                f"animal={animal} | "
                f"disease={symptom_data['disease']} | "
                f"risk={result.get('risk_level') if result else 'ERROR'}"
            )

            return f"END {message}"

    # ── BRANCH B: Report sick animal ──────────────────────────────
    if main_choice == "2":

        if step == 1:
            update_session(sessionId, current_step=2, branch="B")
            return (
                "CON Select sick animal:\n"
                "1. Cattle\n"
                "2. Goats\n"
                "3. Sheep\n"
                "4. Poultry"
            )

        animal_choice = parts[1] if len(parts) > 1 else ""

        if step == 2:
            if animal_choice not in ANIMAL_MAP:
                return (
                    "CON Invalid. Select animal:\n"
                    "1. Cattle\n"
                    "2. Goats\n"
                    "3. Sheep\n"
                    "4. Poultry"
                )
            animal = ANIMAL_MAP[animal_choice]
            update_session(
                sessionId,
                current_step=3,
                animal_type=animal
            )

            if animal == "Cattle":
                return (
                    "CON Main symptom:\n"
                    "1. Sores on mouth or feet\n"
                    "2. Lumps on skin\n"
                    "3. Fever, not eating\n"
                    "4. Sudden deaths\n"
                    "5. Other"
                )
            elif animal in ["Goats", "Sheep"]:
                return (
                    "CON Main symptom:\n"
                    "1. Coughing, runny nose\n"
                    "2. Mouth sores\n"
                    "3. Sudden deaths\n"
                    "4. Eye or nose discharge\n"
                    "5. Other"
                )
            else:
                return (
                    "CON Main symptom:\n"
                    "1. Dying suddenly\n"
                    "2. Swollen head\n"
                    "3. Not moving\n"
                    "4. Twisted necks\n"
                    "5. Other"
                )

        symptom_choice = parts[2] if len(parts) > 2 else ""

        if step == 3:
            session = get_session(sessionId)
            animal  = session.get("animal_type", "Cattle")
            symptom_data = SYMPTOM_MAP.get(animal, {}).get(
                symptom_choice,
                {"symptom": "other", "rolling_boost": 1,
                 "disease": "unknown"}
            )
            update_session(
                sessionId,
                current_step=4,
                symptom_reported=symptom_data["symptom"]
            )
            return (
                "CON How many animals affected?\n"
                "1. Just one\n"
                "2. Two to five\n"
                "3. More than five\n"
                "4. Whole herd or flock"
            )

        count_choice = parts[3] if len(parts) > 3 else ""

        if step == 4:
            count_map = {
                "1": "just_one",
                "2": "two_to_five",
                "3": "more_than_five",
                "4": "whole_herd"
            }
            count_label = count_map.get(count_choice, "unknown")
            update_session(
                sessionId,
                current_step=5,
                number_affected=count_label
            )

            session = get_session(sessionId)
            animal  = session.get("animal_type", "Cattle")

            disease_hint = {
                "mouth_sores":  "Foot and Mouth Disease",
                "skin_lumps":   "Lumpy Skin Disease",
                "cough_runny":  "PPR (Peste des Petits Ruminants)",
                "sudden_death": "possible viral infection",
                "sudden_deaths":"possible viral infection",
                "fever_no_eat": "possible CBPP infection",
                "eye_discharge":"possible PPR infection",
                "other":        "unknown — vet visit needed"
            }.get(session.get("symptom_reported", "other"),
                  "unknown — vet visit needed")

            return (
                f"END Thank you for reporting.\n"
                f"Possible: {disease_hint}.\n"
                f"Isolate sick animals now.\n"
                f"Contact your LGA vet office.\n"
                f"Report has been logged."
            )

    # ── Fallback ──────────────────────────────────────────────────
    return (
        "END Invalid input.\n"
        "Please dial again and\n"
        "select 1, 2 or 3."
    )
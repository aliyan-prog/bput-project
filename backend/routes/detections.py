from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
import os


# Load environment variables
load_dotenv()


router = APIRouter()


# MongoDB connection
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://127.0.0.1:27017"
)

client = MongoClient(
    MONGO_URI
)

db = client["factory_safety"]

detections = db["detections"]
alerts = db["alerts"]


# MongoDB indexes
detections.create_index([
    ("camera_id", 1),
    ("event_type", 1),
    ("timestamp", -1)
])

alerts.create_index([
    ("camera_id", 1),
    ("event_type", 1),
    ("status", 1),
    ("timestamp", -1)
])


# Detection data model
class Detection(BaseModel):

    camera_id: str

    location: str

    event_type: str

    confidence: float = Field(
        ...,
        ge=0,
        le=1
    )

    bbox: List[float]


# Safety events that should be stored
SAFETY_EVENTS = {

    "NO_HELMET",
    "NO_VEST",
    "NO_GLOVES",
    "NO_SHOES",
    "SMOKE",
    "FIRE"
}


# Alert severity mapping
ALERT_LEVELS = {

    "NO_HELMET": "WARNING",

    "NO_VEST": "WARNING",

    "NO_GLOVES": "WARNING",

    "NO_SHOES": "WARNING",

    "SMOKE": "HIGH",

    "FIRE": "CRITICAL",

    # Person detection is not an alert
    "PERSON": "NONE"
}


# Settings
ALERT_COOLDOWN = 10

CONFIDENCE_THRESHOLD = 0.50


@router.post("/detect")
def receive_detection(data: Detection):

    # Convert event type to uppercase
    event_type = data.event_type.upper()


    # Ignore low-confidence detections
    if data.confidence < CONFIDENCE_THRESHOLD:

        return {

            "success": True,

            "message": "Detection ignored due to low confidence",

            "detection_id": None,

            "alert_id": None,

            "severity": "NONE",

            "alert_created": False
        }


    # Ignore non-safety detections
    if event_type not in SAFETY_EVENTS:

        return {

            "success": True,

            "message": "Non-safety detection ignored",

            "detection_id": None,

            "alert_id": None,

            "severity": "NONE",

            "alert_created": False
        }


    # Get alert severity
    severity = ALERT_LEVELS.get(
        event_type,
        "NONE"
    )


    # Current timestamp
    timestamp = datetime.now(timezone.utc)


    # Time for cooldown check
    cooldown_time = (
        timestamp -
        timedelta(
            seconds=ALERT_COOLDOWN
        )
    )


    # Check for recent active alert
    recent_alert = alerts.find_one(
        {
            "camera_id": data.camera_id,

            "event_type": event_type,

            "status": "ACTIVE",

            "timestamp": {
                "$gte": cooldown_time
            }
        }
    )


    # Detection data
    detection_data = {

        "camera_id": data.camera_id,

        "location": data.location,

        "event_type": event_type,

        "confidence": data.confidence,

        "bbox": data.bbox,

        "severity": severity,

        "timestamp": timestamp
    }


    # Save only safety detection
    result = detections.insert_one(
        detection_data
    )


    alert_id = None


    # Create alert if no recent active alert exists
    if recent_alert is None:

        alert_data = {

            "camera_id": data.camera_id,

            "event_type": event_type,

            "location": data.location,

            "severity": severity,

            "confidence": data.confidence,

            "status": "ACTIVE",

            "timestamp": timestamp,

            "message": f"{event_type} detected!"
        }


        alert_result = alerts.insert_one(
            alert_data
        )


        alert_id = str(
            alert_result.inserted_id
        )


    return {

        "success": True,

        "message": "Safety detection received",

        "detection_id": str(
            result.inserted_id
        ),

        "alert_id": alert_id,

        "severity": severity,

        "alert_created": (
            alert_id is not None
        )
    }
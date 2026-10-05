from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from routes.detections import router as detection_router
from bson import ObjectId
from dotenv import load_dotenv
import os


# Load environment variables
load_dotenv()


app = FastAPI(title="Factory Safety AI")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# MongoDB connection
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://127.0.0.1:27017"
)

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client["factory_safety"]

detections = db["detections"]
alerts = db["alerts"]


# Connect detection router
app.include_router(detection_router)


# Home
@app.get("/")
def home():

    return {
        "message": "Factory Safety AI Backend is running"
    }


# Health check
@app.get("/health")
def health():

    try:

        client.admin.command("ping")

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception as e:

        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Get all detections
@app.get("/detections")
def get_detections():

    records = list(
        detections.find(
            {},
            {"_id": 0}
        ).sort(
            "timestamp",
            -1
        )
    )

    return {
        "count": len(records),
        "detections": records
    }


# Get all alerts
@app.get("/alerts")
def get_alerts():

    records = list(
        alerts.find({})
        .sort("timestamp", -1)
    )

    for record in records:

        record["_id"] = str(
            record["_id"]
        )

        if "object_name" in record and "event_type" not in record:

            record["event_type"] = record["object_name"]

        if "message" not in record:

            record["message"] = (
                record["event_type"] + " detected!"
            )

    return {
        "count": len(records),
        "alerts": records
    }


# Resolve an alert
@app.put("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str):

    try:

        object_id = ObjectId(alert_id)

    except Exception:

        return {
            "success": False,
            "message": "Invalid alert ID"
        }

    result = alerts.update_one(
        {
            "_id": object_id
        },
        {
            "$set": {
                "status": "RESOLVED"
            }
        }
    )

    if result.matched_count == 0:

        return {
            "success": False,
            "message": "Alert not found"
        }

    return {
        "success": True,
        "message": "Alert resolved",
        "alert_id": alert_id,
        "status": "RESOLVED"
    }


# Get active alerts
@app.get("/alerts/active")
def get_active_alerts():

    records = list(
        alerts.find(
            {
                "status": "ACTIVE"
            }
        ).sort(
            "timestamp",
            -1
        )
    )

    for record in records:

        record["_id"] = str(
            record["_id"]
        )

        if "object_name" in record and "event_type" not in record:

            record["event_type"] = record["object_name"]

        if "message" not in record:

            record["message"] = (
                record["event_type"] + " detected!"
            )

    return {
        "count": len(records),
        "alerts": records
    }


# Get alert history
@app.get("/alerts/history")
def get_alert_history():

    records = list(
        alerts.find({})
        .sort(
            "timestamp",
            -1
        )
    )

    for record in records:

        record["_id"] = str(
            record["_id"]
        )

        if "object_name" in record and "event_type" not in record:

            record["event_type"] = record["object_name"]

        if "message" not in record:

            record["message"] = (
                record["event_type"] + " detected!"
            )

    return {
        "count": len(records),
        "alerts": records
    }


# Detection statistics
@app.get("/statistics")
def get_statistics():

    total_detections = detections.count_documents({})

    total_alerts = alerts.count_documents({})

    fire_count = detections.count_documents({
        "event_type": "FIRE"
    })

    smoke_count = detections.count_documents({
        "event_type": "SMOKE"
    })

    helmet_count = detections.count_documents({
        "event_type": "NO_HELMET"
    })

    vest_count = detections.count_documents({
        "event_type": "NO_VEST"
    })

    gloves_count = detections.count_documents({
        "event_type": "NO_GLOVES"
    })

    shoes_count = detections.count_documents({
        "event_type": "NO_SHOES"
    })

    critical_alerts = alerts.count_documents({
        "severity": "CRITICAL"
    })

    warning_alerts = alerts.count_documents({
        "severity": "WARNING"
    })

    high_alerts = alerts.count_documents({
        "severity": "HIGH"
    })

    active_alerts = alerts.count_documents({
        "status": "ACTIVE"
    })

    resolved_alerts = alerts.count_documents({
        "status": "RESOLVED"
    })

    return {

        "total_detections": total_detections,

        "total_alerts": total_alerts,

        "active_alerts": active_alerts,

        "resolved_alerts": resolved_alerts,

        "hazards": {

            "fire": fire_count,

            "smoke": smoke_count
        },

        "ppe_violations": {

            "no_helmet": helmet_count,

            "no_vest": vest_count,

            "no_gloves": gloves_count,

            "no_shoes": shoes_count
        },

        "alerts_by_severity": {

            "critical": critical_alerts,

            "high": high_alerts,

            "warning": warning_alerts
        }
    }
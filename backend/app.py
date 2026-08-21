from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

import os
from supabase import create_client, Client


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
FRONTEND_DIR = PROJECT_DIR / "frontend"

ENV_FILE = PROJECT_DIR / ".env"

print("=" * 60)
print("PROJECT CONFIGURATION")
print("=" * 60)

print("BASE_DIR     :", BASE_DIR)
print("PROJECT_DIR  :", PROJECT_DIR)
print("FRONTEND_DIR :", FRONTEND_DIR)
print("ENV FILE     :", ENV_FILE)
print("ENV EXISTS   :", ENV_FILE.exists())

print("HISTORY HTML :", FRONTEND_DIR / "history.html")
print("HTML EXISTS  :", (FRONTEND_DIR / "history.html").exists())
print("JS EXISTS    :", (FRONTEND_DIR / "script.js").exists())
print("CSS EXISTS   :", (FRONTEND_DIR / "style.css").exists())

print("=" * 60)


# ============================================================
# LOAD .ENV
# ============================================================

# IMPORTANT:
# Your .env is in:
#
# History and Analytics/
#     .env
#     backend/
#         app.py
#     frontend/
#
# Therefore we explicitly load the .env from PROJECT_DIR.

load_dotenv(dotenv_path=ENV_FILE, override=True)


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = os.getenv(
    "SUPABASE_TABLE",
    "traffic_history"
)


print("SUPABASE_URL   :", "LOADED" if SUPABASE_URL else "MISSING")
print("SUPABASE_KEY   :", "LOADED" if SUPABASE_KEY else "MISSING")
print("SUPABASE_TABLE :", SUPABASE_TABLE)

print("=" * 60)


# ============================================================
# CHECK SUPABASE CONFIGURATION
# ============================================================

if not SUPABASE_URL:
    raise RuntimeError(
        "SUPABASE_URL is missing from .env. "
        "Make sure .env is located in the project root."
    )

if not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_KEY is missing from .env."
    )


# ============================================================
# SUPABASE CLIENT
# ============================================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

print("SUPABASE CLIENT : CONNECTED")
print("=" * 60)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="DEMETER Traffic Intelligence API",
    version="2.0.0",
    description="Supabase-powered Traffic History and Analytics API"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SUPABASE HELPER
# ============================================================

def get_all_records(
    location=None,
    mode=None,
    start_date=None,
    end_date=None
):
    """
    Fetch traffic records from Supabase.

    Filtering is performed through Supabase.
    """

    query = supabase.table(
        SUPABASE_TABLE
    ).select("*")

    # --------------------------------------------------------
    # LOCATION FILTER
    # --------------------------------------------------------

    if location:
        query = query.eq(
            "location",
            location
        )

    # --------------------------------------------------------
    # MODE FILTER
    # --------------------------------------------------------

    if mode:
        query = query.eq(
            "mode",
            mode
        )

    # --------------------------------------------------------
    # DATE FILTERS
    # --------------------------------------------------------

    if start_date:
        query = query.gte(
            "timestamp",
            f"{start_date} 00:00:00"
        )

    if end_date:
        query = query.lte(
            "timestamp",
            f"{end_date} 23:59:59"
        )

    # --------------------------------------------------------
    # ORDER
    # --------------------------------------------------------

    query = query.order(
        "timestamp",
        desc=True
    )

    response = query.execute()

    return response.data or []


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "success": True,
        "message": "DEMETER Traffic Intelligence API is running",
        "database": "Supabase",
        "table": SUPABASE_TABLE,
        "history": "/history",
        "api_history": "/api/history",
        "docs": "/docs"
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    try:

        response = (
            supabase
            .table(SUPABASE_TABLE)
            .select("id")
            .limit(1)
            .execute()
        )

        return {
            "success": True,
            "status": "healthy",
            "database": "Supabase",
            "database_connected": True,
            "table": SUPABASE_TABLE
        }

    except Exception as e:

        return {
            "success": False,
            "status": "unhealthy",
            "database": "Supabase",
            "database_connected": False,
            "error": str(e)
        }


# ============================================================
# CONFIG
# ============================================================

@app.get("/config")
def config():

    return {
        "success": True,
        "version": "2.0.0",
        "database": "Supabase",
        "table": SUPABASE_TABLE
    }


# ============================================================
# HISTORY PAGE
# ============================================================

@app.get("/history")
def history_page():

    html_file = FRONTEND_DIR / "history.html"

    if not html_file.exists():

        return {
            "success": False,
            "error": "history.html not found",
            "expected_path": str(html_file)
        }

    return FileResponse(
        path=str(html_file),
        media_type="text/html"
    )


# ============================================================
# GET HISTORY
# ============================================================

@app.get("/api/history")
def get_history(
    location: str | None = None,
    mode: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None
):

    try:

        rows = get_all_records(
            location=location,
            mode=mode,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "success": True,
            "database": "Supabase",
            "data": rows
        }

    except Exception as e:

        return {
            "success": False,
            "data": [],
            "error": str(e)
        }


# ============================================================
# POST HISTORY
# ============================================================

@app.post("/api/history")
def add_history(record: dict):

    try:

        timestamp = record.get("timestamp")

        if not timestamp:

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        new_record = {

            "timestamp": timestamp,

            "location": record.get(
                "location",
                "Unknown"
            ),

            "event": record.get(
                "event",
                "Normal Traffic"
            ),

            "mode": record.get(
                "mode",
                "AUTO"
            ),

            "vehicle_count": record.get(
                "vehicle_count",
                0
            ),

            "car": record.get(
                "car",
                0
            ),

            "bike": record.get(
                "bike",
                0
            ),

            "bus": record.get(
                "bus",
                0
            ),

            "truck": record.get(
                "truck",
                0
            ),

            "ambulance": record.get(
                "ambulance",
                0
            ),

            "traffic_level": record.get(
                "traffic_level",
                "Low"
            ),

            "inbound": record.get(
                "inbound",
                0
            ),

            "outbound": record.get(
                "outbound",
                0
            ),

            "details": record.get(
                "details",
                ""
            )
        }

        response = (
            supabase
            .table(SUPABASE_TABLE)
            .insert(new_record)
            .execute()
        )

        inserted = response.data or []

        return {
            "success": True,
            "database": "Supabase",
            "data": inserted
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# ANALYTICS FILTERS
# ============================================================

@app.get("/api/analytics/filters")
def analytics_filters():

    try:

        rows = get_all_records()

        locations = sorted(
            list(
                set(
                    row.get("location")
                    for row in rows
                    if row.get("location")
                )
            )
        )

        modes = sorted(
            list(
                set(
                    row.get("mode")
                    for row in rows
                    if row.get("mode")
                )
            )
        )

        return {

            "success": True,

            "locations": locations,

            "modes": modes
        }

    except Exception as e:

        return {

            "success": False,

            "locations": [],

            "modes": [],

            "error": str(e)
        }


# ============================================================
# ANALYTICS SUMMARY
# ============================================================

@app.get("/api/analytics/summary")
def analytics_summary(
    location: str | None = None,
    mode: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None
):

    try:

        rows = get_all_records(
            location=location,
            mode=mode,
            start_date=start_date,
            end_date=end_date
        )

        # ----------------------------------------------------
        # EMPTY RESULT
        # ----------------------------------------------------

        if not rows:

            return {

                "success": True,

                "total_volume": 0,

                "peak_hour": "--",

                "emergency_clearances": 0,

                "current_mode": "--"
            }

        # ----------------------------------------------------
        # TOTAL VEHICLES
        # ----------------------------------------------------

        total_volume = sum(

            int(row.get("vehicle_count") or 0)

            for row in rows
        )

        # ----------------------------------------------------
        # EMERGENCY EVENTS
        # ----------------------------------------------------

        emergency = 0

        for row in rows:

            ambulance = int(
                row.get("ambulance") or 0
            )

            event = str(
                row.get("event") or ""
            ).lower()

            if ambulance > 0 or "emergency" in event:

                emergency += 1

        # ----------------------------------------------------
        # PEAK TRAFFIC
        # ----------------------------------------------------

        peak = max(

            rows,

            key=lambda row:
                int(
                    row.get("vehicle_count") or 0
                )
        )

        peak_timestamp = peak.get(
            "timestamp"
        )

        peak_hour = "--"

        if peak_timestamp:

            try:

                # Handles:
                # 2026-08-21 12:00:00

                peak_hour = datetime.fromisoformat(
                    str(peak_timestamp).replace(
                        "Z",
                        ""
                    )
                ).strftime("%H:%M")

            except Exception:

                try:

                    peak_hour = str(
                        peak_timestamp
                    )[11:16]

                except Exception:

                    peak_hour = "--"

        # ----------------------------------------------------
        # CURRENT MODE
        # ----------------------------------------------------

        current_mode = rows[0].get(
            "mode",
            "--"
        )

        return {

            "success": True,

            "total_volume": total_volume,

            "peak_hour": peak_hour,

            "emergency_clearances": emergency,

            "current_mode": current_mode
        }

    except Exception as e:

        return {

            "success": False,

            "total_volume": 0,

            "peak_hour": "--",

            "emergency_clearances": 0,

            "current_mode": "--",

            "error": str(e)
        }


# ============================================================
# ANALYTICS TREND
# ============================================================

@app.get("/api/analytics/trend")
def analytics_trend(
    location: str | None = None,
    mode: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None
):

    try:

        rows = get_all_records(
            location=location,
            mode=mode,
            start_date=start_date,
            end_date=end_date
        )

        hourly = {}

        for row in rows:

            timestamp = str(
                row.get("timestamp") or ""
            )

            if len(timestamp) < 13:
                continue

            hour = timestamp[11:13]

            hour_label = f"{hour}:00"

            count = int(
                row.get("vehicle_count") or 0
            )

            hourly[hour_label] = (
                hourly.get(hour_label, 0)
                + count
            )

        data = [

            {
                "hour": hour,
                "vehicle_count": hourly[hour]
            }

            for hour in sorted(hourly.keys())
        ]

        return {

            "success": True,

            "data": data
        }

    except Exception as e:

        return {

            "success": False,

            "data": [],

            "error": str(e)
        }


# ============================================================
# ANALYTICS DISTRIBUTION
# ============================================================

@app.get("/api/analytics/distribution")
def analytics_distribution(
    location: str | None = None,
    mode: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None
):

    try:

        rows = get_all_records(
            location=location,
            mode=mode,
            start_date=start_date,
            end_date=end_date
        )

        distribution = {}

        for row in rows:

            location_name = row.get(
                "location"
            )

            if not location_name:
                continue

            count = int(
                row.get("vehicle_count") or 0
            )

            distribution[location_name] = (

                distribution.get(
                    location_name,
                    0
                )

                + count
            )

        data = [

            {
                "location": location_name,
                "vehicle_count": count
            }

            for location_name, count
            in sorted(
                distribution.items(),
                key=lambda item: item[1],
                reverse=True
            )
        ]

        return {

            "success": True,

            "data": data
        }

    except Exception as e:

        return {

            "success": False,

            "data": [],

            "error": str(e)
        }


# ============================================================
# ANALYTICS FLOW
# ============================================================

@app.get("/api/analytics/flow")
def analytics_flow(
    location: str | None = None,
    mode: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None
):

    try:

        rows = get_all_records(
            location=location,
            mode=mode,
            start_date=start_date,
            end_date=end_date
        )

        hourly = {}

        for row in rows:

            timestamp = str(
                row.get("timestamp") or ""
            )

            if len(timestamp) < 13:
                continue

            hour = timestamp[11:13]

            hour_label = f"{hour}:00"

            inbound = int(
                row.get("inbound") or 0
            )

            outbound = int(
                row.get("outbound") or 0
            )

            if hour_label not in hourly:

                hourly[hour_label] = {

                    "inbound": 0,

                    "outbound": 0
                }

            hourly[hour_label][
                "inbound"
            ] += inbound

            hourly[hour_label][
                "outbound"
            ] += outbound

        data = [

            {
                "hour": hour,

                "inbound":
                    hourly[hour]["inbound"],

                "outbound":
                    hourly[hour]["outbound"]
            }

            for hour in sorted(hourly.keys())
        ]

        return {

            "success": True,

            "data": data
        }

    except Exception as e:

        return {

            "success": False,

            "data": [],

            "error": str(e)
        }


# ============================================================
# DATABASE TEST
# ============================================================

@app.get("/api/database-test")
def database_test():

    try:

        response = (
            supabase
            .table(SUPABASE_TABLE)
            .select("*")
            .limit(5)
            .execute()
        )

        rows = response.data or []

        return {

            "success": True,

            "database": "Supabase",

            "table": SUPABASE_TABLE,

            "connected": True,

            "rows_returned": len(rows),

            "data": rows
        }

    except Exception as e:

        return {

            "success": False,

            "database": "Supabase",

            "table": SUPABASE_TABLE,

            "connected": False,

            "error": str(e)
        }


# ============================================================
# STATIC FRONTEND
# ============================================================

app.mount(
    "/frontend",
    StaticFiles(
        directory=str(FRONTEND_DIR)
    ),
    name="frontend"
)


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False
    )
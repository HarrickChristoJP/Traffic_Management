import warnings
warnings.filterwarnings("ignore")

import os
import cv2
import pandas as pd
import tempfile
import joblib
import numpy as np
from fastapi import FastAPI, UploadFile, File, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from ultralytics import YOLO
from typing import List, Dict, Any, Optional
import time
import json
import threading
import asyncio
from dataclasses import dataclass
import serial
import serial.tools.list_ports

# ====== CONFIGURATION ======
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models")

# Model paths
VEHICLE_MODEL_PATH = os.path.join(MODEL_DIR, "yolov8n.pt")        # COCO model for vehicles
AMBULANCE_MODEL_PATH = os.path.join(MODEL_DIR, "best.pt")         # Custom ambulance model
TRAFFIC_MODEL_PATH = os.path.join(MODEL_DIR, "traffic_gb_8f_v2.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "traffic_encoder_8f_v2.pkl")

# Temporal detection parameters (in REAL frames)
AMBULANCE_CONFIRMATION_THRESHOLD = 15      # minimum consecutive REAL frames
AMBULANCE_TOTAL_THRESHOLD = 25              # minimum total REAL frames
AMBULANCE_CONFIDENCE_THRESHOLD = 0.35       # detection confidence

# Vehicle detection parameters
VEHICLE_CONFIDENCE_THRESHOLD = 0.3

# System configuration
SYSTEM_MODE = os.getenv("SYSTEM_MODE", "UPLOAD")          # "UPLOAD" or "LIVE"
TOTAL_ROADS = int(os.getenv("TOTAL_ROADS", "3"))          # number of roads in intersection
MIN_GREEN_TIME = int(os.getenv("MIN_GREEN_TIME", "10"))   # minimum seconds a road stays green
DECISION_INTERVAL = int(os.getenv("DECISION_INTERVAL", "15"))   # seconds between decisions in LIVE mode

# Serial communication – adjust for your system
SERIAL_PORT = os.getenv("SERIAL_PORT", "COM4")            # Windows: COM4, Linux: /dev/ttyUSB0
SERIAL_BAUD = int(os.getenv("SERIAL_BAUD", "9600"))

# Traffic light durations (seconds)
GREEN_DURATION = 15
YELLOW_DURATION = 3

# Serial stability delay (Windows fix)
SERIAL_WRITE_DELAY = 0.35          # seconds between writes to prevent COM port crash

# ====== LOAD MODELS ======
print("🚦 Initializing Smart Traffic Analysis System...")
print("=" * 50)

try:
    # Load vehicle detection model (COCO)
    vehicle_yolo = YOLO(VEHICLE_MODEL_PATH)
    vehicle_yolo.to("cpu")
    print(f"✅ Vehicle Model: yolov8n.pt")
    print(f"   └─ Classes: {len(vehicle_yolo.names)}")
    print(f"   └─ Vehicle classes: {[vehicle_yolo.names[i] for i in [2, 3, 5, 7]]}")

    # Load ambulance detection model (custom)
    ambulance_yolo = YOLO(AMBULANCE_MODEL_PATH)
    ambulance_yolo.to("cpu")
    print(f"✅ Ambulance Model: best.pt")
    print(f"   └─ Classes: {len(ambulance_yolo.names)}")
    print(f"   └─ Class names: {ambulance_yolo.names}")

    # Load traffic classification model
    traffic_model = joblib.load(TRAFFIC_MODEL_PATH)
    traffic_encoder = joblib.load(ENCODER_PATH)
    print(f"✅ Traffic Classifier: GradientBoosting")
    print(f"   └─ Features: 8, Encoder: LabelEncoder")

    print("=" * 50)
    print("✅ All models loaded successfully.")

except Exception as e:
    print(f"❌ Model loading failed: {e}")
    raise

# ====== SERIAL MANAGER (with lock, delay, and auto‑reconnect) ======
SERIAL_AVAILABLE = True
# pyserial is already imported above, so this try is just for fallback message
if 'serial' not in dir():
    SERIAL_AVAILABLE = False
    print("⚠️ pyserial not installed, will use mock mode")

class ArduinoManager:
    def __init__(self, port=None, baud=9600):
        self.port = port
        self.baud = baud
        self.serial_conn = None
        self.mock = False
        self._lock = asyncio.Lock()          # for async tasks
        self._thread_lock = threading.Lock()  # for thread safety (live mode)

        if port and SERIAL_AVAILABLE:
            self._connect()
        else:
            if not port:
                print("⚠️ No serial port specified, using MOCK mode")
            elif not SERIAL_AVAILABLE:
                print("⚠️ pyserial not available, using MOCK mode")
            self.mock = True

    def _connect(self):
        """Attempt to open serial connection with reset delay."""
        try:
            self.serial_conn = serial.Serial(self.port, self.baud, timeout=1)
            time.sleep(2)   # critical: allow Arduino to reset after USB enumeration
            print(f"✅ Serial connected on {self.port}")
            self.mock = False
        except Exception as e:
            print(f"❌ Serial connection failed: {e}")
            self.serial_conn = None
            self.mock = True

    def _ensure_connection(self):
        """Check if connection is alive; if not, try to reconnect once."""
        if self.mock:
            return False
        if self.serial_conn is None or not self.serial_conn.is_open:
            print("⚠️ Serial connection lost, attempting to reconnect...")
            self._connect()
            return not self.mock
        return True

    async def send_async(self, message: str):
        """Asynchronous send with delay and auto‑reconnect."""
        if self.mock:
            print(f"[MOCK SERIAL] {message}")
            return

        async with self._lock:
            if not self._ensure_connection():
                print("❌ Cannot send, no serial connection. Switching to MOCK.")
                self.mock = True
                return

            try:
                self.serial_conn.write((message + '\n').encode())
                self.serial_conn.flush()
                print(f"📡 Sent to Arduino: {message}")
                # ⭐ CRITICAL: small delay to prevent Windows COM port saturation
                await asyncio.sleep(SERIAL_WRITE_DELAY)
            except Exception as e:
                print(f"❌ Failed to send to Arduino: {e}")
                # Try to reconnect once and retry
                self.serial_conn = None
                if self._ensure_connection():
                    try:
                        self.serial_conn.write((message + '\n').encode())
                        self.serial_conn.flush()
                        print(f"📡 Sent to Arduino (after reconnect): {message}")
                        await asyncio.sleep(SERIAL_WRITE_DELAY)
                    except Exception as e2:
                        print(f"❌ Still failed after reconnect: {e2}")
                        self.mock = True
                else:
                    self.mock = True

    def send_sync(self, message: str):
        """Synchronous send with delay and auto‑reconnect (used by live mode thread)."""
        if self.mock:
            print(f"[MOCK SERIAL] {message}")
            return

        with self._thread_lock:
            if not self._ensure_connection():
                print("❌ Cannot send, no serial connection. Switching to MOCK.")
                self.mock = True
                return

            try:
                self.serial_conn.write((message + '\n').encode())
                self.serial_conn.flush()
                print(f"📡 Sent to Arduino: {message}")
                time.sleep(SERIAL_WRITE_DELAY)   # synchronous delay
            except Exception as e:
                print(f"❌ Failed to send to Arduino: {e}")
                self.serial_conn = None
                if self._ensure_connection():
                    try:
                        self.serial_conn.write((message + '\n').encode())
                        self.serial_conn.flush()
                        print(f"📡 Sent to Arduino (after reconnect): {message}")
                        time.sleep(SERIAL_WRITE_DELAY)
                    except Exception as e2:
                        print(f"❌ Still failed after reconnect: {e2}")
                        self.mock = True
                else:
                    self.mock = True

arduino_manager = ArduinoManager(port=SERIAL_PORT, baud=SERIAL_BAUD)

# ====== DECISION ENGINE ======
@dataclass
class RoadData:
    road: int
    car: float
    bike: float
    bus: float
    truck: float
    total: float
    level: str
    ambulance: bool

def select_best_road(roads_data: List[RoadData], last_served_road: Optional[int] = None) -> tuple:
    """
    Legacy function: returns single best road.
    (Kept for compatibility, not used in new sequential logic.)
    """
    # 1. Ambulance priority
    for r in roads_data:
        if r.ambulance:
            return r.road, "AMBULANCE"

    # 2. Traffic level weights
    level_weight = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

    # 3. Sort by level (desc), then total vehicles (desc)
    sorted_roads = sorted(
        roads_data,
        key=lambda x: (level_weight.get(x.level, 0), x.total),
        reverse=True
    )

    if sorted_roads:
        return sorted_roads[0].road, "MANUAL"
    else:
        return (last_served_road or 1), "MANUAL"

# ====== AI ANALYSIS FUNCTIONS ======
def process_vehicle_detection(frame, model):
    """Process frame with vehicle detection model"""
    results = model(frame, imgsz=416, conf=VEHICLE_CONFIDENCE_THRESHOLD,
                    verbose=False, classes=[2, 3, 5, 7])
    counts = {"car": 0, "bike": 0, "bus": 0, "truck": 0}

    for r in results:
        if r.boxes is None:
            continue
        for cls in r.boxes.cls.cpu().numpy():
            cls = int(cls)
            if cls == 2:      # car
                counts["car"] += 1
            elif cls == 3:    # motorcycle
                counts["bike"] += 1
            elif cls == 5:    # bus
                counts["bus"] += 1
            elif cls == 7:    # truck
                counts["truck"] += 1
    return counts

def check_ambulance_in_frame(frame, model):
    """Check if ambulance is present in a single frame (class index 0)"""
    results = model(frame, imgsz=416, conf=AMBULANCE_CONFIDENCE_THRESHOLD, verbose=False)
    for r in results:
        if r.boxes is None or len(r.boxes) == 0:
            return False, 0.0
        boxes = r.boxes
        if len(boxes) > 0:
            max_conf = boxes.conf.max().item()
            return True, max_conf
    return False, 0.0

class TemporalAmbulanceDetector:
    """Temporal ambulance detection with adaptive thresholds"""
    def __init__(self, consecutive_threshold=15, total_threshold=25, frame_skip=1):
        self.original_consecutive = consecutive_threshold
        self.original_total = total_threshold
        self.frame_skip = max(1, frame_skip)

        self.adjusted_consecutive = max(2, consecutive_threshold // self.frame_skip)
        self.adjusted_total = max(5, total_threshold // self.frame_skip)

        print(f"   [DEBUG] Temporal thresholds - Original: {consecutive_threshold} consecutive, {total_threshold} total")
        print(f"   [DEBUG] Temporal thresholds - Adjusted for skip={frame_skip}: {self.adjusted_consecutive} consecutive, {self.adjusted_total} total")

        self.consecutive_count = 0
        self.total_count = 0
        self.detected = False
        self.max_confidence = 0.0
        self.detection_history = []

    def update(self, frame_idx, detected, confidence=0.0):
        if detected:
            self.consecutive_count += 1
            self.total_count += 1
            self.max_confidence = max(self.max_confidence, confidence)
            self.detection_history.append((frame_idx, True, confidence))

            if (self.consecutive_count >= self.adjusted_consecutive or
                self.total_count >= self.adjusted_total):
                self.detected = True
                print(f"   [DEBUG] Ambulance CONFIRMED at frame {frame_idx}")
                print(f"   [DEBUG]   Consecutive: {self.consecutive_count}/{self.adjusted_consecutive}")
                print(f"   [DEBUG]   Total: {self.total_count}/{self.adjusted_total}")
        else:
            self.consecutive_count = 0
            self.detection_history.append((frame_idx, False, 0.0))

        return self.detected

    def get_summary(self):
        consecutive_detections = []
        current_streak = 0
        for _, detected, _ in self.detection_history:
            if detected:
                current_streak += 1
            else:
                if current_streak > 0:
                    consecutive_detections.append(current_streak)
                    current_streak = 0
        if current_streak > 0:
            consecutive_detections.append(current_streak)
        max_consecutive = max(consecutive_detections) if consecutive_detections else 0
        return {
            "detected": self.detected,
            "total_frames_detected": self.total_count,
            "max_consecutive_frames": max_consecutive,
            "max_confidence": round(self.max_confidence, 3),
            "adjusted_thresholds": {
                "consecutive_frames": self.adjusted_consecutive,
                "total_frames": self.adjusted_total
            },
            "original_thresholds": {
                "consecutive_frames": self.original_consecutive,
                "total_frames": self.original_total,
                "frame_skip": self.frame_skip
            }
        }

def analyze_video_file(video_path: str, road_id: int) -> RoadData:
    """
    Analyze a single video file and return RoadData.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    # Adaptive frame skip
    if total_frames > 300:
        frame_skip = 3
    elif total_frames > 100:
        frame_skip = 2
    else:
        frame_skip = 1

    frame_counts = []
    ambulance_detector = TemporalAmbulanceDetector(
        consecutive_threshold=AMBULANCE_CONFIRMATION_THRESHOLD,
        total_threshold=AMBULANCE_TOTAL_THRESHOLD,
        frame_skip=frame_skip
    )

    processed_frames = 0
    frame_idx = 0

    print(f"📹 Processing road {road_id}: {total_frames} frames | {duration:.1f}s | FPS: {fps}")
    print(f"   └─ Frame skip: {frame_skip}")

    start_processing = time.time()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_skip != 0:
            frame_idx += 1
            continue

        vehicle_counts = process_vehicle_detection(frame, vehicle_yolo)
        frame_counts.append(vehicle_counts)

        ambulance_detected, confidence = check_ambulance_in_frame(frame, ambulance_yolo)
        ambulance_detector.update(processed_frames, ambulance_detected, confidence)

        processed_frames += 1
        frame_idx += 1

        if ambulance_detector.detected and processed_frames >= 50:
            break

    cap.release()
    processing_time = time.time() - start_processing
    print(f"   └─ Processed {processed_frames} frames in {processing_time:.2f}s")

    if not frame_counts:
        raise ValueError(f"No frames processed for road {road_id}")

    # Average counts
    df_counts = pd.DataFrame(frame_counts)
    avg_counts = df_counts.mean()

    car = avg_counts.get("car", 0)
    bike = avg_counts.get("bike", 0)
    bus = avg_counts.get("bus", 0)
    truck = avg_counts.get("truck", 0)

    # Calculate features for traffic model
    heavy = bus + truck
    light = car + bike
    total = heavy + light
    heavy_ratio = heavy / (total + 1e-6)

    FEATURE_COLS = ["Car", "Bike", "Bus", "Truck", "Heavy", "Light", "Total", "Heavy_Ratio"]
    X = pd.DataFrame([[
        car, bike, bus, truck,
        heavy, light, total, heavy_ratio
    ]], columns=FEATURE_COLS)

    try:
        traffic_pred_encoded = traffic_model.predict(X)
        traffic_level = traffic_encoder.inverse_transform(traffic_pred_encoded)[0]
    except Exception as e:
        traffic_level = "MEDIUM"
        print(f"Traffic prediction error for road {road_id}: {e}")

    ambulance_summary = ambulance_detector.get_summary()

    return RoadData(
        road=road_id,
        car=car,
        bike=bike,
        bus=bus,
        truck=truck,
        total=total,
        level=traffic_level,
        ambulance=ambulance_summary["detected"]
    )

# ====== BACKGROUND TRAFFIC SEQUENCE ======
async def run_traffic_sequence(roads_data: List[RoadData]):
    """
    Execute the full traffic light sequence based on priority order:
    1. Ambulance roads first (all of them, in order of detection)
    2. Then normal roads sorted by traffic level (HIGH > MEDIUM > LOW) and total count
    Each road gets GREEN for GREEN_DURATION seconds.
    Between roads, the upcoming road gets YELLOW for YELLOW_DURATION seconds.
    After the last road, a RESET command is sent (all red).
    """
    # Separate ambulance and normal roads
    ambulance_roads = [r for r in roads_data if r.ambulance]
    normal_roads = [r for r in roads_data if not r.ambulance]

    # Sort normal roads by traffic level (weight) and total count descending
    level_weight = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    normal_roads.sort(key=lambda x: (level_weight.get(x.level, 0), x.total), reverse=True)

    # Final queue: all ambulance roads (preserve their order) followed by sorted normal roads
    road_queue = ambulance_roads + normal_roads

    if not road_queue:
        print("⚠️ No roads to process in sequence.")
        return

    print("🚦 Traffic sequence order:")
    for i, r in enumerate(road_queue):
        print(f"   {i+1}. Road {r.road} {'(AMBULANCE)' if r.ambulance else ''} - {r.level}")

    # Iterate through the queue
    for i, road in enumerate(road_queue):
        # Send GREEN for current road
        amb_flag = 1 if road.ambulance else 0
        cmd = (f"SET,{road.road},GREEN,{amb_flag},{GREEN_DURATION},"
               f"{int(round(road.car))},{int(round(road.bike))},"
               f"{int(round(road.bus))},{int(round(road.truck))}")
        await arduino_manager.send_async(cmd)

        # If this is the last road, just wait and then reset
        if i == len(road_queue) - 1:
            await asyncio.sleep(GREEN_DURATION)
            await arduino_manager.send_async("RESET")
            break

        # Wait for the green duration
        await asyncio.sleep(GREEN_DURATION)

        # Send YELLOW for the next road
        next_road = road_queue[i + 1]
        yellow_cmd = f"SET,{next_road.road},YELLOW,0,{YELLOW_DURATION},0,0,0,0"
        await arduino_manager.send_async(yellow_cmd)
        await asyncio.sleep(YELLOW_DURATION)

        # Loop will then send GREEN for next road

# ====== LIVE MODE BACKGROUND THREAD ======
class LiveIntersectionController:
    def __init__(self, total_roads: int, decision_interval: int, min_green_time: int):
        self.total_roads = total_roads
        self.decision_interval = decision_interval
        self.min_green_time = min_green_time
        self.last_switch_time = 0
        self.current_road = 1
        self.running = True
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(f"🔴 LIVE mode started with {self.total_roads} roads, decision interval {self.decision_interval}s")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

    def _run(self):
        # Open cameras (assuming indexes 0,1,2,...)
        caps = []
        for i in range(self.total_roads):
            cap = cv2.VideoCapture(i)
            if not cap.isOpened():
                print(f"⚠️ Could not open camera {i}. Check connections.")
            caps.append(cap)

        while self.running:
            roads_data = []
            for i, cap in enumerate(caps):
                road_id = i + 1
                if cap is None or not cap.isOpened():
                    continue
                ret, frame = cap.read()
                if not ret:
                    print(f"⚠️ Failed to capture from camera {i}")
                    continue

                vehicle_counts = process_vehicle_detection(frame, vehicle_yolo)
                car, bike, bus, truck = vehicle_counts["car"], vehicle_counts["bike"], vehicle_counts["bus"], vehicle_counts["truck"]
                total = car + bike + bus + truck
                heavy = bus + truck
                light = car + bike
                heavy_ratio = heavy / (total + 1e-6)

                FEATURE_COLS = ["Car", "Bike", "Bus", "Truck", "Heavy", "Light", "Total", "Heavy_Ratio"]
                X = pd.DataFrame([[
                    car, bike, bus, truck,
                    heavy, light, total, heavy_ratio
                ]], columns=FEATURE_COLS)

                try:
                    traffic_pred_encoded = traffic_model.predict(X)
                    traffic_level = traffic_encoder.inverse_transform(traffic_pred_encoded)[0]
                except:
                    traffic_level = "MEDIUM"

                ambulance_detected, _ = check_ambulance_in_frame(frame, ambulance_yolo)

                roads_data.append(RoadData(
                    road=road_id,
                    car=car,
                    bike=bike,
                    bus=bus,
                    truck=truck,
                    total=total,
                    level=traffic_level,
                    ambulance=ambulance_detected
                ))

            if not roads_data:
                print("⚠️ No road data available. Skipping decision.")
                time.sleep(self.decision_interval)
                continue

            # In live mode we still use the old single‑road decision (for simplicity)
            selected_road, mode = select_best_road(roads_data, self.current_road)

            now = time.time()
            if mode == "AMBULANCE":
                self.current_road = selected_road
                self.last_switch_time = now
                # Send immediate command (using sync send)
                road_info = next(r for r in roads_data if r.road == selected_road)
                cmd = (f"SET,{selected_road},GREEN,1,{GREEN_DURATION},"
                       f"{int(round(road_info.car))},{int(round(road_info.bike))},"
                       f"{int(round(road_info.bus))},{int(round(road_info.truck))}")
                arduino_manager.send_sync(cmd)
            else:
                if selected_road != self.current_road and (now - self.last_switch_time) >= self.min_green_time:
                    self.current_road = selected_road
                    self.last_switch_time = now
                    road_info = next(r for r in roads_data if r.road == selected_road)
                    cmd = (f"SET,{selected_road},GREEN,0,{GREEN_DURATION},"
                           f"{int(round(road_info.car))},{int(round(road_info.bike))},"
                           f"{int(round(road_info.bus))},{int(round(road_info.truck))}")
                    arduino_manager.send_sync(cmd)
                elif selected_road == self.current_road:
                    road_info = next(r for r in roads_data if r.road == self.current_road)
                    cmd = (f"SET,{self.current_road},GREEN,0,{GREEN_DURATION},"
                           f"{int(round(road_info.car))},{int(round(road_info.bike))},"
                           f"{int(round(road_info.bus))},{int(round(road_info.truck))}")
                    arduino_manager.send_sync(cmd)
                else:
                    print(f"⏳ Minimum green time not reached. Keeping road {self.current_road}")
                    # Still send update for current road
                    road_info = next(r for r in roads_data if r.road == self.current_road)
                    cmd = (f"SET,{self.current_road},GREEN,0,{GREEN_DURATION},"
                           f"{int(round(road_info.car))},{int(round(road_info.bike))},"
                           f"{int(round(road_info.bus))},{int(round(road_info.truck))}")
                    arduino_manager.send_sync(cmd)

            time.sleep(self.decision_interval)

        # Release cameras
        for cap in caps:
            if cap:
                cap.release()

# Start live mode if configured
if SYSTEM_MODE.upper() == "LIVE":
    live_controller = LiveIntersectionController(TOTAL_ROADS, DECISION_INTERVAL, MIN_GREEN_TIME)
    live_controller.start()
else:
    live_controller = None
    print("📤 SYSTEM MODE: UPLOAD (use /analyze-intersection endpoint)")

# ====== FASTAPI SETUP ======
app = FastAPI(
    title="Smart Traffic Analysis API",
    description="Real‑time traffic analysis with temporal ambulance confirmation and full intersection sequencing",
    version="4.1"
)

templates = Jinja2Templates(directory="templates")

# ====== API ENDPOINTS ======
@app.post("/analyze-intersection")
async def analyze_intersection(files: List[UploadFile] = File(...), background_tasks: BackgroundTasks = None):
    """
    Upload mode: Accept multiple video files (one per road).
    Files order corresponds to road IDs (file 1 = road 1, file 2 = road 2, ...).
    The system analyzes each video, determines traffic conditions and ambulance presence,
    then launches a background task that executes the full traffic light sequence
    (all roads in priority order) by sending commands to the Arduino.
    """
    if len(files) < 1 or len(files) > 4:
        raise HTTPException(status_code=400, detail="Upload between 1 and 4 video files")

    roads_data = []

    for idx, file in enumerate(files):
        road_id = idx + 1
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        temp.write(await file.read())
        temp.close()

        try:
            road_result = analyze_video_file(temp.name, road_id)
            roads_data.append(road_result)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed for road {road_id}: {str(e)}")
        finally:
            os.remove(temp.name)

    # Launch background task to execute the traffic sequence
    background_tasks.add_task(run_traffic_sequence, roads_data)

    # Prepare immediate response
    response = {
        "status": "processing",
        "message": "Traffic analysis complete. Full intersection sequence started.",
        "roads_data": [
            {
                "road": r.road,
                "car": round(r.car, 2),
                "bike": round(r.bike, 2),
                "bus": round(r.bus, 2),
                "truck": round(r.truck, 2),
                "total": round(r.total, 2),
                "level": r.level,
                "ambulance": r.ambulance
            } for r in roads_data
        ],
        "sequence": {
            "green_duration": GREEN_DURATION,
            "yellow_duration": YELLOW_DURATION
        }
    }

    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    # FIX: use request as keyword argument (newer Starlette/FastAPI)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html"
    )

@app.get("/debug-models")
async def debug_models():
    """Debug endpoint to check model classes"""
    vehicle_classes = {}
    ambulance_classes = {}

    if hasattr(vehicle_yolo, 'names'):
        vehicle_classes = {i: vehicle_yolo.names[i] for i in [2, 3, 5, 7]}

    if hasattr(ambulance_yolo, 'names'):
        ambulance_classes = dict(ambulance_yolo.names)

    return {
        "vehicle_model_classes": vehicle_classes,
        "ambulance_model_classes": ambulance_classes,
        "ambulance_model_class_count": len(ambulance_classes),
        "note": "Ambulance model should be single-class (class 0 = ambulance)"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "4.1",
        "models_loaded": True,
        "system_mode": SYSTEM_MODE,
        "total_roads": TOTAL_ROADS,
        "temporal_logic_enabled": True,
        "serial_connected": not arduino_manager.mock,
        "ambulance_thresholds": {
            "consecutive_frames": AMBULANCE_CONFIRMATION_THRESHOLD,
            "total_frames": AMBULANCE_TOTAL_THRESHOLD,
            "confidence": AMBULANCE_CONFIDENCE_THRESHOLD
        }
    }

@app.get("/")
async def root():
    return {
        "message": "🚦 Smart Traffic Analysis API v4.1",
        "description": "Real‑time traffic analysis with temporal ambulance confirmation and full intersection sequencing",
        "system_mode": SYSTEM_MODE,
        "total_roads": TOTAL_ROADS,
        "features": [
            "Temporal ambulance detection (adaptive thresholds)",
            "Multi‑road priority scheduling (ambulance first, then traffic level)",
            "Full traffic light sequence: GREEN → YELLOW → next GREEN → ... → RESET",
            f"Green duration: {GREEN_DURATION}s, Yellow duration: {YELLOW_DURATION}s",
            "Background task execution (non‑blocking)",
            "Serial communication with 2‑second delay after open (Arduino reset fix)",
            "✅ Added 350ms delay after each write to prevent Windows COM port crash",
            "✅ Automatic serial reconnection on failure"
        ],
        "quote": "Industrial‑grade intersection control with AI vision and bulletproof serial handling."
    }

@app.post("/set-mode")
async def set_mode(mode: str, roads: Optional[int] = None):
    """
    Change system mode dynamically (UPLOAD or LIVE). Optionally update TOTAL_ROADS.
    """
    global SYSTEM_MODE, TOTAL_ROADS, live_controller
    mode = mode.upper()
    if mode not in ["UPLOAD", "LIVE"]:
        raise HTTPException(status_code=400, detail="Mode must be UPLOAD or LIVE")

    if roads is not None:
        if roads < 1 or roads > 4:
            raise HTTPException(status_code=400, detail="Roads must be between 1 and 4")
        TOTAL_ROADS = roads

    if mode == "LIVE" and SYSTEM_MODE != "LIVE":
        if live_controller:
            live_controller.stop()
        live_controller = LiveIntersectionController(TOTAL_ROADS, DECISION_INTERVAL, MIN_GREEN_TIME)
        live_controller.start()
    elif mode == "UPLOAD" and SYSTEM_MODE == "LIVE":
        if live_controller:
            live_controller.stop()
            live_controller = None

    SYSTEM_MODE = mode
    return {"message": f"System mode set to {mode}", "total_roads": TOTAL_ROADS}

# ====== RUN THE APP ======
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
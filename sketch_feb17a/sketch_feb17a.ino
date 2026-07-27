/*
  SMART TRAFFIC CONTROLLER – AI EXECUTOR (FINAL INDUSTRIAL)
  - Fixed Windows COM reset issue
  - Serial timeout + clean read
  - Fail‑safe reset on every command
  - RX debug for verification
  - Supports full intersection sequencing from AI
*/                                                                                                                                                       

#include <Wire.h>
#include <LiquidCrystal_I2C.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);   // adjust address if needed

// -------------------- Pin Definitions --------------------
const int redPins[]    = {2, 5, 8, 11};
const int yellowPins[] = {3, 6, 9, 12};
const int greenPins[]  = {4, 7, 10, 13};
const int MAX_ROADS = 4;

// -------------------- State Machine --------------------
enum SystemState {
  WAITING,
  ACTIVE,
  AMBULANCE,
  FAIL_SAFE
};
SystemState currentState = WAITING;

// -------------------- Active Command --------------------
struct Command {
  int road;
  int color;          // 0=RED, 1=YELLOW, 2=GREEN
  unsigned long duration;  // milliseconds
  bool hasDuration;
};
Command activeCommand = {0, 0, 0, false};
unsigned long commandStartTime = 0;

// -------------------- Ambulance --------------------
int ambulanceRoad = 0;

// -------------------- Fail‑safe --------------------
unsigned long lastMsgTime = 0;
const unsigned long TIMEOUT_MS = 10000;
bool failSafeTriggered = false;

// -------------------- Duplicate Suppression --------------------
String lastCommand = "";

// -------------------- Vehicle Counts Display --------------------
int carCount = 0, bikeCount = 0, busCount = 0, truckCount = 0;
bool haveCounts = false;
enum CountsPhase { CP_OFF, CP_CAR_BIKE, CP_BUS_TRUCK };
CountsPhase countsPhase = CP_OFF;
unsigned long countsPhaseStartTime = 0;
const unsigned long COUNTS_PHASE_DURATION = 1500;

// -------------------- LCD Optimization --------------------
unsigned long lastDisplayedRemaining = 9999;

// -------------------- Setup --------------------
void setup() {
  Serial.begin(9600);
  Serial.setTimeout(50);           // ⭐ short timeout
  delay(2000);                      // ⭐ allow USB to settle after reset

  lcd.init();
  lcd.backlight();

  // Initialize all roads – all start RED
  for (int i = 0; i < MAX_ROADS; i++) {
    pinMode(redPins[i], OUTPUT);
    pinMode(yellowPins[i], OUTPUT);
    pinMode(greenPins[i], OUTPUT);
    digitalWrite(redPins[i], HIGH);
    digitalWrite(yellowPins[i], LOW);
    digitalWrite(greenPins[i], LOW);
  }

  bootSequence();
  updateDisplayWaiting();

  lastMsgTime = millis();
  Serial.println("AI Traffic Executor Ready");
}

void bootSequence() {
  lcd.clear();
  lcd.setCursor(0, 0); lcd.print("Traffic Project");
  lcd.setCursor(0, 1); lcd.print("Using AI");
  delay(2000);
  lcd.clear();
  lcd.setCursor(0, 0); lcd.print("By Team");
  lcd.setCursor(0, 1); lcd.print("GenZ Coderz");
  delay(2000);
}

// -------------------- Main Loop --------------------
void loop() {
  // ⭐ robust serial reading with debug
  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    line.trim();

    if (line.length() == 0) return;

    Serial.print("RX: ");
    Serial.println(line);   // you will see this in Serial Monitor

    if (line != lastCommand) {
      lastCommand = line;
      processCommand(line);
    }
  }

  // Update state machines
  switch (currentState) {
    case ACTIVE:
      updateActiveState();
      break;
    case AMBULANCE:
      // No automatic changes
      break;
    default:
      break;
  }

  // Non‑blocking vehicle counts display
  updateCountsDisplay();

  // Fail‑safe check
  checkFailSafe();

  delay(10);
}

// -------------------- Command Processing --------------------
void processCommand(String cmd) {
  // ⭐ reset fail‑safe timer on every command
  failSafeTriggered = false;
  lastMsgTime = millis();

  const int MAX_PARTS = 9;
  String parts[MAX_PARTS];
  int partCount = 0;
  int start = 0;
  for (int i = 0; i < cmd.length() && partCount < MAX_PARTS; i++) {
    if (cmd.charAt(i) == ',') {
      parts[partCount++] = cmd.substring(start, i);
      start = i + 1;
    }
  }
  if (start < cmd.length() && partCount < MAX_PARTS) {
    parts[partCount++] = cmd.substring(start);
  }

  if (partCount < 2) return;

  String cmdType = parts[0];
  cmdType.toUpperCase();

  if (cmdType == "RESET") {
    currentState = WAITING;
    setAllRed();
    updateDisplayWaiting();
    haveCounts = false;
    countsPhase = CP_OFF;
    failSafeTriggered = false;
    lastDisplayedRemaining = 9999;
    Serial.println("ACK: Reset");
    return;
  }

  if (cmdType == "SET" && partCount >= 4) {
    int road = safeToInt(parts[1]);
    String colorStr = parts[2];
    int ambFlag = safeToInt(parts[3]);

    if (road < 1 || road > MAX_ROADS) {
      Serial.println("ERROR: Invalid road");
      return;
    }

    int color;
    if (colorStr.equalsIgnoreCase("GREEN")) color = 2;
    else if (colorStr.equalsIgnoreCase("YELLOW")) color = 1;
    else if (colorStr.equalsIgnoreCase("RED")) color = 0;
    else {
      Serial.println("ERROR: Invalid color");
      return;
    }

    unsigned long duration = 0;
    bool hasDuration = false;
    if (partCount >= 5) {
      duration = (unsigned long)safeToInt(parts[4]) * 1000;
      hasDuration = true;
    }

    // Parse counts if present
    haveCounts = false;
    if (partCount >= 9) {
      carCount = safeToInt(parts[5]);
      bikeCount = safeToInt(parts[6]);
      busCount = safeToInt(parts[7]);
      truckCount = safeToInt(parts[8]);
      haveCounts = true;
      countsPhase = CP_CAR_BIKE;
      countsPhaseStartTime = millis();
      lcd.clear();
      lcd.setCursor(0, 0); lcd.print("Car:"); lcd.print(carCount);
      lcd.setCursor(8, 0); lcd.print("Bike:"); lcd.print(bikeCount);
    }

    if (ambFlag == 1) {
      currentState = AMBULANCE;
      ambulanceRoad = road;
      setAmbulanceMode(road);
      updateDisplayAmbulance(road);
      Serial.print("ACK: Ambulance road "); Serial.println(road);
    } else {
      currentState = ACTIVE;
      activeCommand.road = road;
      activeCommand.color = color;
      activeCommand.duration = duration;
      activeCommand.hasDuration = hasDuration;
      commandStartTime = millis();
      setRoadColor(road, color);
      if (!haveCounts) {
        if (hasDuration)
          updateDisplayActiveWithTime(road, color, duration / 1000);
        else
          updateDisplayActiveNoTime(road, color);
      }
    }
    return;
  }

  Serial.println("ERROR: Unknown command");
}

// -------------------- Active State with Countdown --------------------
void updateActiveState() {
  if (!activeCommand.hasDuration) return;

  unsigned long elapsed = millis() - commandStartTime;
  if (elapsed >= activeCommand.duration) {
    currentState = WAITING;
    setAllRed();
    updateDisplayWaiting();
    haveCounts = false;
    countsPhase = CP_OFF;
    lastDisplayedRemaining = 9999;
  } else {
    if (!haveCounts || countsPhase == CP_OFF) {
      unsigned long remainingSec = (activeCommand.duration - elapsed) / 1000;
      if (remainingSec != lastDisplayedRemaining) {
        lastDisplayedRemaining = remainingSec;
        updateDisplayActiveWithTime(activeCommand.road, activeCommand.color, remainingSec);
      }
    }
  }
}

// -------------------- Non‑blocking Vehicle Counts Display --------------------
void updateCountsDisplay() {
  if (!haveCounts) return;

  unsigned long now = millis();
  switch (countsPhase) {
    case CP_CAR_BIKE:
      if (now - countsPhaseStartTime >= COUNTS_PHASE_DURATION) {
        countsPhase = CP_BUS_TRUCK;
        countsPhaseStartTime = now;
        lcd.clear();
        lcd.setCursor(0, 0); lcd.print("Bus:"); lcd.print(busCount);
        lcd.setCursor(8, 0); lcd.print("Truck:"); lcd.print(truckCount);
      }
      break;

    case CP_BUS_TRUCK:
      if (now - countsPhaseStartTime >= COUNTS_PHASE_DURATION) {
        haveCounts = false;
        countsPhase = CP_OFF;
        switch (currentState) {
          case WAITING:    updateDisplayWaiting(); break;
          case ACTIVE:
            if (activeCommand.hasDuration) {
              unsigned long remaining = (activeCommand.duration - (millis() - commandStartTime)) / 1000;
              updateDisplayActiveWithTime(activeCommand.road, activeCommand.color, remaining);
              lastDisplayedRemaining = remaining;
            } else {
              updateDisplayActiveNoTime(activeCommand.road, activeCommand.color);
            }
            break;
          case AMBULANCE:  updateDisplayAmbulance(ambulanceRoad); break;
          case FAIL_SAFE:  updateDisplayFailSafe(); break;
          default: break;
        }
      }
      break;

    default:
      break;
  }
}

// -------------------- LED Control --------------------
void setAllRed() {
  for (int i = 0; i < MAX_ROADS; i++) {
    digitalWrite(redPins[i], HIGH);
    digitalWrite(yellowPins[i], LOW);
    digitalWrite(greenPins[i], LOW);
  }
}

void setRoadColor(int road, int color) {
  int idx = road - 1;
  for (int i = 0; i < MAX_ROADS; i++) {
    if (i == idx) {
      switch (color) {
        case 0:
          digitalWrite(redPins[i], HIGH);
          digitalWrite(yellowPins[i], LOW);
          digitalWrite(greenPins[i], LOW);
          break;
        case 1:
          digitalWrite(redPins[i], LOW);
          digitalWrite(yellowPins[i], HIGH);
          digitalWrite(greenPins[i], LOW);
          break;
        case 2:
          digitalWrite(redPins[i], LOW);
          digitalWrite(yellowPins[i], LOW);
          digitalWrite(greenPins[i], HIGH);
          break;
      }
    } else {
      digitalWrite(redPins[i], HIGH);
      digitalWrite(yellowPins[i], LOW);
      digitalWrite(greenPins[i], LOW);
    }
  }
}

void setAmbulanceMode(int road) {
  int idx = road - 1;
  for (int i = 0; i < MAX_ROADS; i++) {
    if (i == idx) {
      digitalWrite(redPins[i], LOW);
      digitalWrite(yellowPins[i], LOW);
      digitalWrite(greenPins[i], HIGH);
    } else {
      digitalWrite(redPins[i], HIGH);
      digitalWrite(yellowPins[i], LOW);
      digitalWrite(greenPins[i], LOW);
    }
  }
}

// -------------------- LCD Display Helpers --------------------
void updateDisplayWaiting() {
  lcd.clear();
  lcd.setCursor(0, 0); lcd.print("AI Traffic Ctrl");
  lcd.setCursor(0, 1); lcd.print("All RED");
}

void updateDisplayActiveWithTime(int road, int color, unsigned long remainingSec) {
  lcd.setCursor(0, 0);
  lcd.print("Road "); lcd.print(road); lcd.print(": ");
  switch (color) {
    case 0: lcd.print("RED   "); break;
    case 1: lcd.print("YELLOW"); break;
    case 2: lcd.print("GREEN "); break;
  }
  lcd.setCursor(0, 1);
  lcd.print("Time: "); lcd.print(remainingSec); lcd.print("s   ");
}

void updateDisplayActiveNoTime(int road, int color) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Road "); lcd.print(road); lcd.print(": ");
  switch (color) {
    case 0: lcd.print("RED"); break;
    case 1: lcd.print("YELLOW"); break;
    case 2: lcd.print("GREEN"); break;
  }
  lcd.setCursor(0, 1);
  lcd.print("Others RED");
}

void updateDisplayAmbulance(int road) {
  lcd.clear();
  lcd.setCursor(0, 0); lcd.print("!!! AMBULANCE !!!");
  lcd.setCursor(0, 1); lcd.print("Road "); lcd.print(road); lcd.print(" GREEN");
}

void updateDisplayFailSafe() {
  lcd.clear();
  lcd.setCursor(0, 0); lcd.print("FAIL-SAFE MODE");
  lcd.setCursor(0, 1); lcd.print("All RED");
}

// -------------------- Fail‑safe --------------------
void checkFailSafe() {
  if (currentState != AMBULANCE && !failSafeTriggered &&
      (millis() - lastMsgTime > TIMEOUT_MS)) {
    currentState = FAIL_SAFE;
    failSafeTriggered = true;
    setAllRed();
    updateDisplayFailSafe();
    Serial.println("WARN: Fail-safe activated");
  }
}

// -------------------- Safe Integer Conversion --------------------
int safeToInt(String s) {
  s.trim();
  if (s.length() == 0) return 0;
  long val = 0;
  bool neg = false;
  int i = 0;
  if (s.charAt(0) == '-') { neg = true; i = 1; }
  for (; i < s.length(); i++) {
    char c = s.charAt(i);
    if (c < '0' || c > '9') break;
    val = val * 10 + (c - '0');
    if (val > 1000000) break;
  }
  if (neg) val = -val;
  return (int)val;
}
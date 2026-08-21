#  DEMETER – Traffic Intelligence & History Analytics

> A web-based traffic intelligence and analytics system for monitoring, storing, and analyzing historical traffic data.

##  Overview

**DEMETER** is a Traffic Intelligence and History Analytics platform designed to provide real-time access to historical traffic telemetry and analytical insights.

The system collects traffic data such as vehicle counts, traffic levels, vehicle categories, emergency events, and traffic flow, stores the data in **Supabase PostgreSQL**, and presents the results through an interactive web dashboard.

---

##  Features

-  Traffic volume analytics
-  24-hour traffic trend analysis
-  Location-based traffic distribution
-  Inbound and outbound flow analysis
-  Emergency vehicle/event tracking
-  Traffic mode monitoring
-  Location, mode, and date filtering
-  Cloud database using Supabase
-  FastAPI REST API
-  Historical traffic records
-  Database connection testing
-  Automatic Swagger API documentation

---

##  System Architecture

```text
┌──────────────────────────────┐
│          FRONTEND            │
│                              │
│   HTML + CSS + JavaScript    │
│        history.html          │
│        style.css             │
│        script.js             │
└──────────────┬───────────────┘
               │
               │ HTTP / REST API
               ▼
┌──────────────────────────────┐
│           FASTAPI            │
│                              │
│          backend/app.py      │
│                              │
│  • REST APIs                 │
│  • Filtering                 │
│  • Analytics                 │
│  • Data Processing           │
└──────────────┬───────────────┘
               │
               │ Supabase API
               ▼
┌──────────────────────────────┐
│          SUPABASE            │
│                              │
│      PostgreSQL Database     │
│                              │
│       traffic_history        │
└──────────────────────────────┘

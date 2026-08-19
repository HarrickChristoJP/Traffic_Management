import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pandas as pd

SUPABASE_URL = "https://fpiwqwxbsttmlektirgg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwaXdxd3hic3R0bWxla3RpcmdnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODYxNDk2NDcsImV4cCI6MjEwMTcyNTY0N30.U0ubME9xN4SPi1NMeZ_vODbpeYNCrS4_4VT2FWaUlzE"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("🚨 Traffic Management Prototype")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_data" not in st.session_state:
    st.session_state.user_data = None
if "show_cctv" not in st.session_state:
    st.session_state.show_cctv = False

# Login Section
if not st.session_state.logged_in:
    st.subheader("Personnel Login")
    badge_input = st.text_input("Enter your Badge ID:")
    if st.button("Login"):
        if not badge_input:
            st.warning("Please enter a badge ID.")
        else:
            try:
                response = supabase.table("users").select("*").eq("badge_id", badge_input.strip()).execute()
                if len(response.data) == 0:
                    st.error("❌ Access Denied.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.user_data = response.data[0]
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
else:
    user = st.session_state.user_data
    st.success(f"✅ Welcome, {user['name']}!")
    st.info(f"**Badge:** {user['badge_id']} | **Role:** {user['role']} | **Home Zone:** {user['zone_id'] if user['zone_id'] else 'HQ / Organization'}")
    
    # 1. LIVE TRAFFIC MONITORING
    st.subheader("📊 Live Traffic Dashboard")
    if st.button("View Live Traffic Monitoring (All Zones)"):
        try:
            feeds = supabase.table("traffic_feeds").select("*").execute().data
            if not feeds:
                st.warning("No traffic feeds available in Supabase yet.")
            else:
                st.dataframe(feeds, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()

    # 2. CONGESTION ANALYTICS & CHARTS
    st.subheader("📈 Congestion Analytics & Trends")
    st.caption("Visualizing traffic density, peak hours, and zone congestion levels.")

    try:
        analytics_response = supabase.table("traffic_feeds").select("*").execute()
        analytics_data = analytics_response.data

        if not analytics_data:
            analytics_data = [
                {"location_name": "Main Street Junction", "zone_id": "Zone_1", "vehicle_count": 45, "congestion_level": 85},
                {"location_name": "Downtown Avenue", "zone_id": "Zone_1", "vehicle_count": 30, "congestion_level": 60},
                {"location_name": "Highway 42 Exit", "zone_id": "Zone_2", "vehicle_count": 75, "congestion_level": 95},
                {"location_name": "Central Park Crossing", "zone_id": "Zone_2", "vehicle_count": 20, "congestion_level": 40},
                {"location_name": "Industrial Parkway", "zone_id": "Zone_3", "vehicle_count": 60, "congestion_level": 70}
            ]

        df = pd.DataFrame(analytics_data)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("##### Congestion Index by Junction")
            if 'congestion_level' in df.columns and 'location_name' in df.columns:
                chart_data = df.set_index('location_name')['congestion_level']
                st.bar_chart(chart_data)

        with col_b:
            st.markdown("##### Vehicle Count Distribution")
            if 'vehicle_count' in df.columns and 'location_name' in df.columns:
                vehicle_data = df.set_index('location_name')['vehicle_count']
                st.bar_chart(vehicle_data)

    except Exception as chart_err:
        st.warning(f"Could not load analytics charts: {chart_err}")

    st.divider()

    # 3. CCTV VIDEO FEED INTEGRATION (Triggered via Button)
    st.subheader("📹 Live CCTV Feeds & Archives")
    st.caption("Click the button below to load camera selections, dates, and live traffic streams.")

    if not st.session_state.show_cctv:
        if st.button("🔄 View live/ archive feeds"):
            st.session_state.show_cctv = True
            st.rerun()
    else:
        if st.button("❌ Hide Video Feeds"):
            st.session_state.show_cctv = False
            st.rerun()

        try:
            cctv_response = supabase.table("traffic_feeds").select("*").execute()
            cameras = cctv_response.data

            if not cameras:
                cameras = [
                    {"location_name": "Main Street Junction", "zone_id": "Zone_1", "congestion_level": "High", "camera_url": "mock_stream_1"},
                    {"location_name": "Highway 42 Exit", "zone_id": "Zone_2", "congestion_level": "Severe", "camera_url": "mock_stream_2"},
                    {"location_name": "Industrial Parkway", "zone_id": "Zone_3", "congestion_level": "Moderate", "camera_url": "mock_stream_3"}
                ]

            cam_options = {f"{cam.get('location_name', 'Camera')} ({cam.get('zone_id', 'Zone')})": cam for cam in cameras}
            
            selected_cam_label = st.selectbox("Select Junction / Camera Location", list(cam_options.keys()))
            selected_date = st.date_input("Select Archive Date", datetime.now())
            
            selected_cam = cam_options[selected_cam_label]

            col1, col2 = st.columns([2, 1])
            with col1:
                traffic_video_url = "https://assets.mixkit.co/videos/preview/mixkit-cars-crossing-a-busy-intersection-41580-large.mp4"
                st.video(traffic_video_url)
                st.caption(f"Streaming from source: {selected_cam.get('camera_url', 'Traffic Cam 01')} | Date: {selected_date}")

            with col2:
                st.markdown("### Camera Diagnostics")
                st.metric("Zone", selected_cam.get('zone_id', 'N/A'))
                st.metric("Congestion Level", str(selected_cam.get('congestion_level', 'Normal')))
                st.status("Status: Online (AI Model Ready)", state="complete")

        except Exception as cctv_err:
            st.error(f"Error loading CCTV feeds: {cctv_err}")

    st.divider()

    # 4. MANUAL SIGNAL OVERRIDE & GRANULAR CONTROLS
    st.subheader("🎛️ Manual Signal Override & Timing Control")
    st.caption("Initiate manual intervention and configure granular phase durations for the override corridor.")

    with st.form("vip_override_form"):
        vip_name = st.text_input("VIP / Convoy / Incident Identifier")
        target_zone = st.selectbox("Target Zone for Operation", ["Zone_1", "Zone_2", "Zone_3", "HQ / All Zones"])
        override_action = st.selectbox("Override Action", ["Force Green Corridor (All Signals)", "Clear Route & Hold Red"])
        
        st.markdown("---")
        st.markdown("##### 🚦 Granular Phase Duration Customization (Active during override)")
        
        col1, col2 = st.columns(2)
        with col1:
            green_duration = st.slider("Green Light Phase (seconds)", min_value=10, max_value=120, value=45)
            yellow_duration = st.slider("Yellow Light Phase (seconds)", min_value=3, max_value=10, value=5)
        with col2:
            red_duration = st.slider("Red Light Phase (seconds)", min_value=10, max_value=120, value=30)
            green_wave = st.checkbox("Enable Multi-Junction Green-Wave Corridor", value=True)

        trigger_override = st.form_submit_button("Deploy Manual Override & Timing Configuration")
        
        if trigger_override:
            if not vip_name:
                st.warning("Please enter a VIP or incident identifier.")
            else:
                try:
                    action_summary = (
                        f"Override ({override_action}) for {vip_name} | "
                        f"Timings -> Green: {green_duration}s, Yellow: {yellow_duration}s, "
                        f"Red: {red_duration}s, Green-Wave: {green_wave}"
                    )
                    log_data = {
                        "user_badge": user['badge_id'],
                        "user_name": user['name'],
                        "user_role": user['role'],
                        "home_zone": user['zone_id'] if user['zone_id'] else "HQ",
                        "target_zone": target_zone,
                        "action_details": action_summary,
                        "timestamp": str(datetime.now())
                    }
                    supabase.table("activity_logs").insert(log_data).execute()
                    st.success(f"🚨 Manual Override & Granular Timing Deployed in {target_zone} by {user['name']}!")
                except Exception as log_err:
                    st.error(f"Action executed, but failed to save activity log: {log_err}")

    st.divider()

    # 5. ACTIVITY LOGS & NOTIFICATIONS (Segregated for Higher Officials)
    st.subheader("🔔 Activity Logs & Notifications")
    st.caption("Review your personal actions and monitor other officials' activities across the system.")

    try:
        logs_response = supabase.table("activity_logs").select("user_name, user_role, target_zone, action_details, timestamp, user_badge, home_zone").order("timestamp", desc=True).execute()
        all_logs = logs_response.data

        if not all_logs:
            st.info("No recorded activity logs found.")
        else:
            filtered_logs = []
            user_role = user['role'].lower()
            user_badge = user['badge_id']
            user_home_zone = user['zone_id']

            for log in all_logs:
                if "super" in user_role or ("admin" in user_role and not user_home_zone):
                    filtered_logs.append(log)
                elif "admin" in user_role and user_home_zone and user_home_zone in log['target_zone']:
                    if log['user_role'] != "Area Admin" or log['user_badge'] == user_badge:
                        filtered_logs.append(log)
                elif "field" in user_role or "officer" in user_role:
                    if log['user_badge'] == user_badge:
                        filtered_logs.append(log)

            if not filtered_logs:
                st.info("No relevant notifications or logs for your account.")
            else:
                my_logs = [log for log in filtered_logs if log['user_badge'] == user_badge]
                other_logs = [log for log in filtered_logs if log['user_badge'] != user_badge]

                if "super" in user_role or "admin" in user_role:
                    log_tab1, log_tab2 = st.tabs(["📌 My Activity Logs", "👥 Other Officials' Activity Logs"])
                    
                    with log_tab1:
                        st.markdown(f"### Actions logged by you ({user['name']})")
                        if not my_logs:
                            st.info("You haven't performed any logged actions yet.")
                        else:
                            st.dataframe(my_logs, use_container_width=True)
                            
                    with log_tab2:
                        st.markdown("### Actions logged by other team members / field officers")
                        if not other_logs:
                            st.info("No activity from other officials found.")
                        else:
                            st.dataframe(other_logs, use_container_width=True)
                else:
                    st.markdown("### Your Activity Logs")
                    st.dataframe(my_logs, use_container_width=True)

    except Exception as e:
        st.warning("Activity logs table not found yet in Supabase.")

    st.divider()
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
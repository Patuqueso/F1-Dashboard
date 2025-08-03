import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import fastf1
import datetime
from f1data.telemetry import get_fastest_telemetry, align_telemetry, calculate_time_delta
import matplotlib.pyplot as plt

# Setup cache folder
os.makedirs("data", exist_ok=True)
fastf1.Cache.enable_cache("data")

# Page config
st.set_page_config(page_title="F1 Ghost Comparison", layout="wide")
st.title("\U0001F3CE\uFE0F Ghost Car Qualifying Comparison")

# Season selector
current_year = datetime.datetime.now().year
seasons = list(range(2018, current_year + 1))
season = st.selectbox("Season", seasons, index=len(seasons) - 1)

@st.cache_data
@st.cache_data
def get_race_schedule(season):
    schedule = fastf1.get_event_schedule(season)
    today = datetime.datetime.now().date()

    # Keep only Grand Prix events that have already occurred
    schedule = schedule[schedule['EventName'].str.contains("Grand Prix")]
    schedule = schedule[schedule['EventDate'].dt.date <= today]

    return schedule


schedule = get_race_schedule(season)
race_options = [(i, row['EventName']) for i, row in schedule.iterrows()]
race_choice = st.selectbox("Race", race_options, format_func=lambda x: f"{x[0]} — {x[1]}")

if race_choice:
    round_num = race_choice[0]
    session = fastf1.get_session(season, round_num, 'Q')
    try:
        session.load(laps=True, telemetry=True)
    except Exception as e:
        st.error(f"Failed to load session data: {e}")
        st.stop()


    drivers = sorted(session.laps['Driver'].unique())
    driver_map = {
        code: session.get_driver(code)["FullName"]
        for code in drivers
    }

    col1, col2 = st.columns(2)
    with col1:
        d1 = st.selectbox("Driver 1", drivers, format_func=lambda code: f"{driver_map.get(code, code)} ({code})")
    with col2:
        d2 = st.selectbox("Driver 2", drivers, index=1 if len(drivers) > 1 else 0,
        format_func=lambda code: f"{driver_map.get(code, code)} ({code})")


    if d1 == d2:
        st.warning("Please select two different drivers.")
    else:
        st.subheader("\U0001F4C8 Speed Comparison")

        import traceback
        try:
            tel1 = get_fastest_telemetry(session, d1)
            tel2 = get_fastest_telemetry(session, d2)

            if tel1 is None or tel2 is None:
                st.warning("One of the drivers did not complete a valid qualifying lap.")
                raise ValueError("Missing telemetry")

            result = align_telemetry(tel1, tel2)
            if result is None:
                st.warning("Could not align telemetry data. This may be due to lack of overlapping distances or missing data.")
            else:
                tel1, tel2 = result

            # print("Aligned telemetry data:")
            # print("Driver 1:", d1, "Data Points:", len(tel1))
            # print("Driver 2:", d2, "Data Points:", len(tel2))

            if tel1.empty or tel2.empty:
                st.warning("Aligned telemetry data is empty. Try different drivers or races.")
            else:
                
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(tel1.index, tel1["Speed"], label=d1, color='red')
                ax.plot(tel2.index, tel2["Speed"], label=d2, color='blue')
                ax.set_title("Fastest Lap Speed by Distance")
                ax.set_xlabel("Distance (m)")
                ax.set_ylabel("Speed (km/h)")
                ax.legend()
                ax.grid(True)
                st.pyplot(fig)

                delta_df = calculate_time_delta(session, d1, d2)
                fig2, ax2 = plt.subplots(figsize=(10, 4))
                ax2.plot(delta_df["Distance"], delta_df["DeltaTime"], color="purple")
                ax2.axhline(0, color='gray', linestyle='--')
                ax2.set_xlabel("Distance (m)")
                ax2.set_ylabel(f"Δt: {d2} - {d1} (s)")
                ax2.set_title("Time Delta by Distance")
                ax2.grid(True)
                st.pyplot(fig2)

        except Exception as e:
            st.text(traceback.format_exc())
            st.error(f"Telemetry comparison failed: {e}")
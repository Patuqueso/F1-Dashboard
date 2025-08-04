import pandas as pd
import numpy as np

def get_fastest_telemetry(session, driver):
    lap = session.laps.pick_drivers(driver).pick_fastest()
    if lap is None:
        return None
    tel = lap.get_telemetry().add_distance()
    return tel[["Distance", "Speed", "SessionTime", "X", "Y"]]

def align_telemetry(tel1, tel2):
    if tel1 is None or tel2 is None or tel1.empty or tel2.empty:
        return None

    # Convert SessionTime to numeric
    tel1["SessionSeconds"] = tel1["SessionTime"].dt.total_seconds()
    tel2["SessionSeconds"] = tel2["SessionTime"].dt.total_seconds()

    # Define common distance
    min_dist = max(tel1["Distance"].min(), tel2["Distance"].min())
    max_dist = min(tel1["Distance"].max(), tel2["Distance"].max())
    common_dist = np.linspace(min_dist, max_dist, 500)

    # Set index and ensure proper sorting
    tel1 = tel1.set_index("Distance").sort_index()
    tel2 = tel2.set_index("Distance").sort_index()

    # Keep only numeric columns for interpolation
    numeric_cols = tel1.select_dtypes(include=[np.number]).columns

    # Explicitly drop SessionTime cause the previous line did not remove it :(
    if "SessionTime" in numeric_cols:
        numeric_cols = numeric_cols.drop("SessionTime")

    tel1_interp = tel1[numeric_cols].reindex(common_dist, method='nearest').interpolate("index")
    tel2_interp = tel2[numeric_cols].reindex(common_dist, method='nearest').interpolate("index")

    # Add back Distance
    tel1_interp["Distance"] = common_dist
    tel2_interp["Distance"] = common_dist

    # Convert SessionSeconds back to timedelta
    tel1_interp["SessionTime"] = pd.to_timedelta(tel1_interp["SessionSeconds"], unit="s")
    tel2_interp["SessionTime"] = pd.to_timedelta(tel2_interp["SessionSeconds"], unit="s")

    # Reset index if needed
    tel1_interp = tel1_interp.reset_index(drop=True)
    tel2_interp = tel2_interp.reset_index(drop=True)

    return tel1_interp, tel2_interp


def calculate_time_delta(session, driver1, driver2):
    lap1 = session.laps.pick_drivers(driver1).pick_fastest()
    lap2 = session.laps.pick_drivers(driver2).pick_fastest()

    if lap1 is None or lap2 is None:
        print("One or both laps not found")
        return pd.DataFrame()

    tel1 = lap1.get_telemetry().add_distance()
    tel2 = lap2.get_telemetry().add_distance()

    if tel1.empty or tel2.empty:
        print("One or both telemetry sets are empty")
        return pd.DataFrame()


    # Shared distance interpolation
    min_dist = max(tel1["Distance"].min(), tel2["Distance"].min())
    max_dist = min(tel1["Distance"].max(), tel2["Distance"].max())
    if min_dist >= max_dist:
        print("No overlapping distance range.")
        return pd.DataFrame()

    common_dist = np.linspace(min_dist, max_dist, 500)

    # Reindex and interpolate
    tel1 = tel1[["Distance", "SessionTime"]].set_index("Distance").reindex(common_dist, method='nearest')
    tel2 = tel2[["Distance", "SessionTime"]].set_index("Distance").reindex(common_dist, method='nearest')

    # Drop NaNs
    if tel1["SessionTime"].isna().any() or tel2["SessionTime"].isna().any():
        print("NaNs found in SessionTime, dropping...")
        tel1 = tel1.dropna(subset=["SessionTime"])
        tel2 = tel2.dropna(subset=["SessionTime"])
        common_dist = tel1.index.intersection(tel2.index)

    # Ensure matching indices
    tel1 = tel1.loc[common_dist]
    tel2 = tel2.loc[common_dist]

    if len(common_dist) == 0 or tel1.empty or tel2.empty:
        print("No valid telemetry after alignment")
        return pd.DataFrame()

    tel1["Time"] = (tel1["SessionTime"] - tel1["SessionTime"].iloc[0]).dt.total_seconds()
    tel2["Time"] = (tel2["SessionTime"] - tel2["SessionTime"].iloc[0]).dt.total_seconds()

    delta = tel2["Time"] - tel1["Time"]

    return pd.DataFrame({"Distance": common_dist[:len(delta)], "DeltaTime": delta})

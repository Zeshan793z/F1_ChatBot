import fastf1

def get_driver_fastest_lap(year, gp, driver_code):
    fastf1.Cache.enable_cache("./data/fastf1_cache")
    session = fastf1.get_session(year, gp, "R")
    session.load()
    laps = session.laps.pick_drivers([driver_code])
    if laps.empty:
        return None
    fastest = laps.pick_fastest()
    return {
        "lap_number": int(fastest['LapNumber']),
        "lap_time": f"{fastest['LapTime'].total_seconds():.3f} seconds",
        "compound": fastest['Compound']
    }

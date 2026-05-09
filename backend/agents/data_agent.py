# import fastf1

# def get_driver_fastest_lap(year, gp, driver_code):
#     fastf1.Cache.enable_cache("./data/fastf1_cache")
#     session = fastf1.get_session(year, gp, "R")
#     session.load()
#     laps = session.laps.pick_drivers([driver_code])
#     if laps.empty:
#         return None
#     fastest = laps.pick_fastest()
#     return {
#         "lap_number": int(fastest['LapNumber']),
#         "lap_time": f"{fastest['LapTime'].total_seconds():.3f} seconds",
#         "compound": fastest['Compound']
#     }


import fastf1
from pathlib import Path
import warnings

warnings.filterwarnings("ignore", message="pick_driver is deprecated")

# Cache can stay in root data folder (shared between runs)
PROJECT_ROOT = Path(__file__).parent.parent.parent
CACHE_DIR = PROJECT_ROOT / "data" / "fastf1_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

print(f"✅ FastF1 cache enabled at: {CACHE_DIR}")

def get_driver_fastest_lap(year: int, gp: str, driver_code: str):
    """Get fastest lap data for a specific driver at a GP"""
    try:
        print(f"📊 Fetching data for {driver_code} at {gp} {year}...")
        session = fastf1.get_session(year, gp, "R")
        session.load(telemetry=False, laps=True, weather=False)
        
        laps = session.laps.pick_drivers([driver_code.upper()])
        
        if laps.empty:
            print(f"⚠️ No laps found for {driver_code}")
            return None
            
        fastest = laps.pick_fastest()
        
        result = {
            "lap_number": int(fastest['LapNumber']),
            "lap_time": f"{fastest['LapTime'].total_seconds():.3f} seconds",
            "compound": str(fastest['Compound']),
            "lap_time_seconds": fastest['LapTime'].total_seconds()
        }
        print(f"✅ Found fastest lap: Lap {result['lap_number']} - {result['lap_time']}")
        return result
    
    except Exception as e:
        print(f"❌ Error fetching fastest lap: {e}")
        return None
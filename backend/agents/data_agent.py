import fastf1
from pathlib import Path
import warnings
from typing import List, Dict, Optional

warnings.filterwarnings("ignore", message="pick_driver is deprecated")
warnings.filterwarnings("ignore", message="The data you are trying to access has not been loaded")

PROJECT_ROOT = Path(__file__).parent.parent.parent
CACHE_DIR = PROJECT_ROOT / "data" / "fastf1_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

print(f"✅ FastF1 cache enabled at: {CACHE_DIR}")

def get_driver_fastest_lap(year: int, gp: str, driver_code: str):
    """Get fastest lap data for a specific driver at a specific GP"""
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
            "lap_time_seconds": fastest['LapTime'].total_seconds(),
            "compound": str(fastest['Compound']),
            "driver": driver_code.upper(),
            "year": year,
            "gp": gp
        }
        print(f"✅ Found fastest lap: Lap {result['lap_number']} - {result['lap_time']}")
        return result
    
    except Exception as e:
        print(f"❌ Error fetching fastest lap for {driver_code} at {gp}: {e}")
        return None


def get_season_fastest_laps(year: int, driver_code: str = None) -> List[Dict]:
    """
    Get fastest lap data for all races in a season
    If driver_code is provided, get only that driver's fastest laps
    """
    try:
        print(f"📊 Fetching {year} season schedule...")
        schedule = fastf1.get_event_schedule(year)
        
        # Filter for race events only (not testing)
        races = schedule[schedule['Session5'] == 'Race']  # Session5 is the Race
        
        results = []
        
        for idx, race in races.iterrows():
            race_name = race['EventName']
            print(f"  Processing: {race_name}")
            
            try:
                session = fastf1.get_session(year, race_name, "R")
                session.load(telemetry=False, laps=True, weather=False)
                
                if driver_code:
                    # Get specific driver's fastest lap
                    laps = session.laps.pick_drivers([driver_code.upper()])
                    if not laps.empty:
                        fastest = laps.pick_fastest()
                        results.append({
                            "gp": race_name,
                            "driver": driver_code.upper(),
                            "lap_number": int(fastest['LapNumber']),
                            "lap_time_seconds": fastest['LapTime'].total_seconds(),
                            "lap_time": f"{fastest['LapTime'].total_seconds():.3f} seconds",
                            "compound": str(fastest['Compound'])
                        })
                else:
                    # Get fastest lap overall for the race
                    fastest_overall = session.laps.pick_fastest()
                    driver = fastest_overall['Driver']
                    results.append({
                        "gp": race_name,
                        "driver": driver,
                        "lap_number": int(fastest_overall['LapNumber']),
                        "lap_time_seconds": fastest_overall['LapTime'].total_seconds(),
                        "lap_time": f"{fastest_overall['LapTime'].total_seconds():.3f} seconds",
                        "compound": str(fastest_overall['Compound'])
                    })
                    
            except Exception as e:
                print(f"    ⚠️ Could not load {race_name}: {str(e)[:100]}")
                continue
        
        print(f"✅ Loaded {len(results)} races from {year}")
        return results
        
    except Exception as e:
        print(f"❌ Error loading season {year}: {e}")
        return []


def get_season_driver_performance(year: int, driver_code: str) -> Dict:
    """
    Get comprehensive performance data for a driver across a season
    """
    try:
        print(f"📊 Analyzing {driver_code}'s performance in {year} season...")
        schedule = fastf1.get_event_schedule(year)
        races = schedule[schedule['Session5'] == 'Race']
        
        performance = {
            "driver": driver_code.upper(),
            "year": year,
            "races": [],
            "fastest_laps": 0,
            "total_fastest_lap_time": 0,
            "avg_lap_time": 0,
            "best_lap_time": float('inf'),
            "best_lap_gp": None
        }
        
        lap_times = []
        
        for idx, race in races.iterrows():
            race_name = race['EventName']
            
            try:
                session = fastf1.get_session(year, race_name, "R")
                session.load(telemetry=False, laps=True, weather=False)
                
                driver_laps = session.laps.pick_drivers([driver_code.upper()])
                if not driver_laps.empty:
                    fastest = driver_laps.pick_fastest()
                    lap_time = fastest['LapTime'].total_seconds()
                    lap_times.append(lap_time)
                    
                    race_data = {
                        "gp": race_name,
                        "fastest_lap": f"{lap_time:.3f} seconds",
                        "lap_number": int(fastest['LapNumber']),
                        "compound": str(fastest['Compound'])
                    }
                    performance["races"].append(race_data)
                    
                    if lap_time < performance["best_lap_time"]:
                        performance["best_lap_time"] = lap_time
                        performance["best_lap_gp"] = race_name
                        
            except Exception as e:
                print(f"  ⚠️ Could not load {race_name}: {str(e)[:50]}")
                continue
        
        if lap_times:
            performance["total_fastest_lap_time"] = sum(lap_times)
            performance["avg_lap_time"] = sum(lap_times) / len(lap_times)
            performance["fastest_laps"] = len(lap_times)
            performance["best_lap_time_formatted"] = f"{performance['best_lap_time']:.3f} seconds"
        
        print(f"✅ Loaded {len(lap_times)} races for {driver_code} in {year}")
        return performance
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"driver": driver_code, "year": year, "error": str(e)}
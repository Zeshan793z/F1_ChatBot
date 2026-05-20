import fastf1
from pathlib import Path

CACHE_DIR = Path("data/fastf1_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

def precache_season(year):
    print(f"\n📦 Pre-caching {year} season...")
    schedule = fastf1.get_event_schedule(year)
    races = schedule[schedule['Session5'] == 'Race']
    
    for idx, race in races.iterrows():
        race_name = race['EventName']
        print(f"  Caching: {race_name}")
        
        try:
            session = fastf1.get_session(year, race_name, "R")
            session.load(telemetry=True, laps=True, weather=True)
            print(f"    ✅ Cached successfully")
        except Exception as e:
            print(f"    ❌ Error: {str(e)[:80]}")
    
    print(f"✅ Finished pre-caching {year}")

# Run for seasons you want
if __name__ == "__main__":
    for year in [2023, 2024, 2025, 2026]:
        precache_season(year)
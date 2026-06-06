# test_weather_data.py
import fastf1
from pathlib import Path

CACHE_DIR = Path("./data/fastf1_cache")
fastf1.Cache.enable_cache(str(CACHE_DIR))

print("Testing weather data for Canadian GP 2026...")
print("=" * 50)

try:
    session = fastf1.get_session(2026, "Canadian Grand Prix", "R")
    session.load(telemetry=False, laps=False, weather=True)
    
    if hasattr(session, 'weather_data') and session.weather_data is not None:
        weather = session.weather_data
        print(f"✅ Weather data found! {len(weather)} records")
        print(f"Columns: {list(weather.columns)}")
        print("\nFirst few rows:")
        print(weather.head())
        
        # Check if any data is actually present
        if 'AirTemp' in weather.columns:
            air_temp = weather['AirTemp'].mean()
            print(f"\n🌡️ Average Air Temperature: {air_temp:.1f}°C")
        else:
            print("\n⚠️ No AirTemp column found")
    else:
        print("❌ No weather data available for this race")
        print("This race may not have weather data in the FastF1 cache yet.")
        
except Exception as e:
    print(f"Error: {e}")
import fastf1
from pathlib import Path

# Use your existing cache directory
cache_dir = Path("./data/fastf1_cache")
fastf1.Cache.enable_cache(str(cache_dir))

print("📥 Downloading Monaco GP 2026 data...")

# Load the session - this will automatically download the data
session = fastf1.get_session(2026, "Monaco Grand Prix", "R")
session.load(telemetry=True, laps=True, weather=True)

print("✅ Monaco GP 2026 data downloaded and cached!")
print(f"📍 Cache location: {cache_dir}/2026/")

# Verify the data
print(f"\n📊 Race Results:")
results = session.results
for idx, row in results.head(5).iterrows():
    print(f"  P{int(row['Position'])}: {row['FullName']} ({row['Abbreviation']}) - {row['TeamName']}")

print(f"\n🏁 Total drivers: {len(results)}")
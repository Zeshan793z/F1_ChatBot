# check_japan_2026.py
import fastf1
from pathlib import Path

fastf1.Cache.enable_cache("./data/fastf1_cache")

session = fastf1.get_session(2026, "Japanese Grand Prix", "R")
session.load(telemetry=False, laps=False, weather=False)

results = session.results

print("Japanese GP 2026 Results:")
print("-" * 50)
for idx, row in results.iterrows():
    print(f"{row['Position']}. {row['Abbreviation']} ({row['FullName']}) - {row['TeamName']}")
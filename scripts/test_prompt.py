import fastf1
from pathlib import Path

fastf1.Cache.enable_cache("./data/fastf1_cache")

session = fastf1.get_session(2026, "Australian Grand Prix", "R")
session.load(laps=True)

fastest = session.laps.pick_fastest()
print(f"Fastest lap driver: {fastest['Driver']}")
print(f"Lap time: {fastest['LapTime'].total_seconds():.3f}s")

# Check if tire compound exists
if 'Compound' in fastest.index:
    print(f"TIRE COMPOUND: {fastest['Compound']}")
else:
    print("TIRE COMPOUND: Not available in this session")
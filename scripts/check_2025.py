import fastf1
from pathlib import Path

# Point this to your existing cache directory
CACHE_DIR = Path("./data/fastf1_cache")
fastf1.Cache.enable_cache(str(CACHE_DIR))

# --- Configuration ---
YEAR = 2026
GP_NAME = "Canadian Grand Prix"
SESSION_TYPE = "R"  # 'R' for Race
DRIVER_TO_CHECK = "ANT"  # Kimi Antonelli's code

print(f"--- Verifying Grid Position Data for {YEAR} {GP_NAME} ---")

try:
    # 1. Load the session
    session = fastf1.get_session(YEAR, GP_NAME, SESSION_TYPE)
    session.load(telemetry=False, laps=False, weather=False)

    # 2. Access the results data
    results = session.results

    # 3. Check if the 'GridPosition' column exists
    if 'GridPosition' in results.columns:
        print("\n✅ SUCCESS: 'GridPosition' column FOUND in session.results.")
        print(f"\n--- Grid Positions for {GP_NAME} ---")
        # Print driver abbreviation and their starting grid position
        for _, driver in results.iterrows():
            print(f"  Driver: {driver['Abbreviation']:3s} | Grid Position: P{int(driver['GridPosition'])}")
        
        # --- Specific check for Kimi Antonelli ---
        driver_data = results[results['Abbreviation'] == DRIVER_TO_CHECK]
        if not driver_data.empty:
            grid_pos = int(driver_data.iloc[0]['GridPosition'])
            print(f"\n🎯 SPECIFIC CHECK: Kimi Antonelli started from P{grid_pos}.")
        else:
            print(f"\n⚠️ Driver '{DRIVER_TO_CHECK}' not found in the session results.")
    else:
        print("\n❌ FAIL: 'GridPosition' column is MISSING from session.results.")
        print("This confirms your cache does not have starting position data for this race.")
        print("\nHere are all the columns that ARE available in your cache for this session:")
        for col in results.columns:
            print(f"  - {col}")

except Exception as e:
    print(f"\n❌ An error occurred: {e}")
"""
Inspect what strategy data is available in your FastF1 cache
"""

import fastf1
from pathlib import Path
import pandas as pd

# Enable cache
CACHE_DIR = Path("./data/fastf1_cache")
fastf1.Cache.enable_cache(str(CACHE_DIR))

def inspect_session(year: int, gp: str):
    """Inspect all available data for a session"""
    print(f"\n{'='*60}")
    print(f"📊 Inspecting: {year} {gp}")
    print('='*60)
    
    try:
        session = fastf1.get_session(year, gp, "R")
        session.load(telemetry=True, laps=True, weather=True)
        
        # 1. Check what lap data is available
        print("\n📋 LAP DATA COLUMNS:")
        print("-" * 40)
        for col in session.laps.columns:
            print(f"  • {col}")
        
        # 2. Check for specific strategy-related columns
        strategy_cols = ['Driver', 'LapNumber', 'LapTime', 'Compound', 'TyreLife', 
                         'PitOutTime', 'PitInTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']
        
        print("\n🎯 STRATEGY-RELATED COLUMNS:")
        print("-" * 40)
        for col in strategy_cols:
            if col in session.laps.columns:
                print(f"  ✅ {col}")
            else:
                print(f"  ❌ {col}")
        
        # 3. Check pit stop data
        print("\n🅿️ PIT STOPS:")
        print("-" * 40)
        pit_stops = session.laps.dropna(subset=['PitInTime'])
        if not pit_stops.empty:
            for idx, pit in pit_stops.iterrows():
                print(f"  Lap {pit['LapNumber']}: {pit['Driver']} - In: {pit['PitInTime']} | Out: {pit['PitOutTime']}")
        else:
            print("  No pit stop data found")
        
        # 4. Check tire data
        print("\n🏁 TIRE DATA:")
        print("-" * 40)
        drivers = session.laps['Driver'].unique()
        for driver in drivers[:5]:  # Limit to first 5 drivers
            driver_laps = session.laps[session.laps['Driver'] == driver]
            compounds = driver_laps['Compound'].unique()
            print(f"  {driver}: {list(compounds)}")
        
        # 5. Check starting grid
        print("\n🏎️ STARTING GRID:")
        print("-" * 40)
        results = session.results
        if 'GridPosition' in results.columns:
            for idx, row in results.head(10).iterrows():
                print(f"  P{int(row['GridPosition'])}: {row['Abbreviation']} ({row['FullName']})")
        else:
            print("  Grid position data not available")
        
        # 6. Check session results for finishing positions
        print("\n🏆 FINISHING POSITIONS:")
        print("-" * 40)
        for idx, row in results.head(10).iterrows():
            print(f"  P{int(row['Position'])}: {row['Abbreviation']} ({row['FullName']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading {year} {gp}: {e}")
        return False


def inspect_all_strategy_data():
    """Inspect strategy data for all races in your cache"""
    
    # Years you have cached
    years = [2026]
    
    # Specific GPs to check
    gps = [
        ("Canadian Grand Prix", 2026)
    ]
    
    for gp, year in gps:
        inspect_session(year, gp)



def extract_strategy_summary(year: int, gp: str, driver_code: str):
    """Extract a summary of strategy data for a specific driver"""
    print(f"\n📊 Strategy Summary for {driver_code} at {year} {gp}")
    print("-" * 50)
    
    try:
        session = fastf1.get_session(year, gp, "R")
        session.load(telemetry=False, laps=True, weather=False)
        
        driver_laps = session.laps[session.laps['Driver'] == driver_code]
        
        if driver_laps.empty:
            print(f"No data found for {driver_code}")
            return
        
        # Get fastest lap
        fastest = driver_laps.pick_fastest()
        
        # Get starting position
        results = session.results
        driver_result = results[results['Abbreviation'] == driver_code]
        start_pos = driver_result['GridPosition'].values[0] if not driver_result.empty else 'Unknown'
        finish_pos = driver_result['Position'].values[0] if not driver_result.empty else 'Unknown'
        
        # Get pit stops
        pit_stops = driver_laps.dropna(subset=['PitInTime'])
        
        # Get tire strategy
        tires_used = driver_laps['Compound'].unique()
        
        print(f"  Starting Position: P{int(start_pos)}")
        print(f"  Finishing Position: P{int(finish_pos)}")
        print(f"  Fastest Lap: Lap {fastest['LapNumber']} - {fastest['LapTime'].total_seconds():.3f}s")
        print(f"  Tires Used: {list(tires_used)}")
        print(f"  Pit Stops: {len(pit_stops)} stops")
        
        if not pit_stops.empty:
            print(f"  Pit Stop Laps: {[int(lap) for lap in pit_stops['LapNumber'].values]}")
        
        # Tire degradation (if we have lap time data)
        laps_over_time = driver_laps[['LapNumber', 'LapTime']].copy()
        laps_over_time['LapTimeSec'] = laps_over_time['LapTime'].dt.total_seconds()
        print(f"  Average Lap Time: {laps_over_time['LapTimeSec'].mean():.3f}s")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("🔍 FastF1 Strategy Data Inspector")
    print("=" * 60)
    
    # Option 1: General inspection
    inspect_all_strategy_data()
    
    # Option 2: Specific driver strategy summary
    print("\n" + "="*60)
    print("📊 SPECIFIC DRIVER STRATEGY SUMMARY")
    print("="*60)
    extract_strategy_summary(2026, "Canadian Grand Prix", "VER")
    

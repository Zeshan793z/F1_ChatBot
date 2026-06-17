"""
Analyze FastF1 cache to see what track/circuit data is available - Without loading sessions
"""

import fastf1
from pathlib import Path
import pandas as pd
import json
import pickle

def analyze_cache_direct():
    """Analyze cache by reading files directly without loading sessions"""
    
    cache_dir = Path("./data/fastf1_cache")
    
    print("=" * 80)
    print("🔍 ANALYZING FASTF1 CACHE DATA (Direct File Reading)")
    print("=" * 80)
    
    cache_analysis = {}
    
    # Years to check
    years = [2026]
    
    for year in years:
        year_dir = cache_dir / str(year)
        if not year_dir.exists():
            continue
        
        print(f"\n📅 {year} Season:")
        print("-" * 40)
        
        # Find all race directories
        for event_dir in year_dir.iterdir():
            if not event_dir.is_dir():
                continue
            
            event_name = event_dir.name.split('_', 1)[-1].replace('_', ' ')
            
            # Look for session info file to read circuit data
            session_info_file = event_dir / "session_info.ff1pkl"
            car_data_file = event_dir / "car_data.ff1pkl"
            laps_file = event_dir / "timing_app_data.ff1pkl"
            
            track_data = {
                'circuit_name': event_name,
                'location': 'Unknown',
                'track_length_km': None,
                'corner_count': None,
                'has_car_data': car_data_file.exists(),
                'has_laps_data': laps_file.exists(),
                'has_session_info': session_info_file.exists()
            }
            
            # Try to read session info for circuit details
            if session_info_file.exists():
                try:
                    with open(session_info_file, 'rb') as f:
                        session_info = pickle.load(f)
                    
                    # Try to extract circuit info
                    if isinstance(session_info, dict):
                        if 'CircuitName' in session_info:
                            track_data['circuit_name'] = session_info['CircuitName']
                        if 'Location' in session_info:
                            track_data['location'] = session_info['Location']
                        if 'Country' in session_info:
                            track_data['location'] = f"{session_info.get('Location', '')}, {session_info['Country']}"
                        if 'Length' in session_info:
                            track_data['track_length_km'] = float(session_info['Length'])
                except Exception as e:
                    pass
            
            # Try to read car data for telemetry info
            if car_data_file.exists():
                try:
                    with open(car_data_file, 'rb') as f:
                        car_data = pickle.load(f)
                    
                    if isinstance(car_data, dict):
                        track_data['drivers_with_telemetry'] = list(car_data.keys())
                        
                        # Try to get track length from distance data
                        for driver, telemetry in car_data.items():
                            if telemetry is not None and hasattr(telemetry, 'columns'):
                                if 'Distance' in telemetry.columns:
                                    max_dist = telemetry['Distance'].max()
                                    if max_dist and max_dist > 0:
                                        track_data['track_length_km'] = round(max_dist / 1000, 3)
                                        break
                except Exception as e:
                    pass
            
            # Print summary
            print(f"  📍 {event_name}:")
            print(f"     Circuit: {track_data['circuit_name']}")
            print(f"     Location: {track_data['location']}")
            if track_data['track_length_km']:
                print(f"     Length: {track_data['track_length_km']:.3f} km")
            print(f"     Has Car Data: {'✅' if track_data['has_car_data'] else '❌'}")
            print(f"     Has Laps Data: {'✅' if track_data['has_laps_data'] else '❌'}")
            
            cache_analysis[f"{year}_{event_name}"] = track_data
    
    return cache_analysis

def check_available_telemetry():
    """Check what telemetry columns are available in car data"""
    
    cache_dir = Path("./data/fastf1_cache")
    
    print("\n" + "=" * 80)
    print("📊 TELEMETRY DATA AVAILABILITY")
    print("=" * 80)
    
    years = [2026]
    
    for year in years:
        year_dir = cache_dir / str(year)
        if not year_dir.exists():
            continue
        
        for event_dir in year_dir.iterdir():
            if not event_dir.is_dir():
                continue
            
            car_data_file = event_dir / "car_data.ff1pkl"
            
            if car_data_file.exists():
                try:
                    with open(car_data_file, 'rb') as f:
                        car_data = pickle.load(f)
                    
                    if isinstance(car_data, dict):
                        for driver, telemetry in car_data.items():
                            if telemetry is not None and hasattr(telemetry, 'columns'):
                                print(f"\n  📊 {event_dir.name.split('_', 1)[-1].replace('_', ' ')} - Driver {driver}:")
                                print(f"     Available telemetry: {list(telemetry.columns)}")
                                break
                except Exception as e:
                    pass

def check_lap_data():
    """Check what lap data is available"""
    
    cache_dir = Path("./data/fastf1_cache")
    
    print("\n" + "=" * 80)
    print("🏁 LAP DATA AVAILABILITY")
    print("=" * 80)
    
    years = [2026]
    
    for year in years:
        year_dir = cache_dir / str(year)
        if not year_dir.exists():
            continue
        
        for event_dir in year_dir.iterdir():
            if not event_dir.is_dir():
                continue
            
            laps_file = event_dir / "timing_app_data.ff1pkl"
            
            if laps_file.exists():
                try:
                    with open(laps_file, 'rb') as f:
                        laps_data = pickle.load(f)
                    
                    if laps_data is not None:
                        print(f"\n  📊 {event_dir.name.split('_', 1)[-1].replace('_', ' ')}:")
                        
                        if hasattr(laps_data, 'columns'):
                            print(f"     Lap data columns: {list(laps_data.columns)}")
                            print(f"     Number of laps: {len(laps_data)}")
                        else:
                            print(f"     Lap data type: {type(laps_data)}")
                except Exception as e:
                    pass

if __name__ == "__main__":
    # Run analysis
    cache_data = analyze_cache_direct()
    
    # Check telemetry columns
    check_available_telemetry()
    
    # Check lap data
    check_lap_data()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    
    circuits_with_length = sum(1 for d in cache_data.values() if d['track_length_km'])
    circuits_with_car_data = sum(1 for d in cache_data.values() if d['has_car_data'])
    
    print(f"Total circuits in cache: {len(cache_data)}")
    print(f"Circuits with track length data: {circuits_with_length}")
    print(f"Circuits with car telemetry: {circuits_with_car_data}")
    
    # Save analysis
    output_file = Path("data/cache_analysis.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(cache_data, f, indent=2, default=str)
    
    print(f"\n💾 Analysis saved to {output_file}")
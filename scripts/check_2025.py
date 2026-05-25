# check_2026_data.py
import fastf1
from pathlib import Path

fastf1.Cache.enable_cache("./data/fastf1_cache")

print("Checking 2026 F1 data...")
print("=" * 50)

try:
    schedule = fastf1.get_event_schedule(2026)
    print(f"\n2026 Events found: {len(schedule)}")
    
    winners = {}
    
    for idx, event in schedule.iterrows():
        event_name = event['EventName']
        session_type = event['Session5'] if 'Session5' in event else 'Race'
        
        if session_type == 'Race':
            try:
                session = fastf1.get_session(2026, event_name, "R")
                session.load()
                results = session.results
                
                if not results.empty:
                    winner = results.iloc[0]
                    winners[event_name] = {
                        'driver': winner['Abbreviation'],
                        'full_name': winner['FullName'],
                        'team': winner['TeamName']
                    }
                    print(f"✅ {event_name}: {winner['FullName']} ({winner['Abbreviation']})")
                else:
                    print(f"⚠️ {event_name}: No results found")
                    
            except Exception as e:
                print(f"❌ {event_name}: Could not load - {str(e)[:50]}")
    
    print("\n" + "=" * 50)
    print("2026 Race Winners Summary:")
    for race, winner in winners.items():
        print(f"  {race}: {winner['full_name']} ({winner['driver']})")
    
    # Determine championship leader (most wins)
    if winners:
        from collections import Counter
        win_counts = Counter([w['driver'] for w in winners.values()])
        print("\n🏆 Current championship leader (most wins):")
        for driver, count in win_counts.most_common(3):
            print(f"  {driver}: {count} wins")
            
except Exception as e:
    print(f"Error: {e}")
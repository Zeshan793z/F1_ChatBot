import fastf1
import json
from pathlib import Path
from typing import List, Dict
import pandas as pd

class F1KnowledgeBase:
    def __init__(self, cache_dir: str = "./data/fastf1_cache"):
        self.cache_dir = Path(cache_dir)
        fastf1.Cache.enable_cache(str(self.cache_dir))
        
    def extract_session_data(self, year: int, gp: str) -> Dict:
        """Extract detailed F1 session data as text"""
        try:
            session = fastf1.get_session(year, gp, "R")
            session.load(telemetry=True, laps=True, weather=True)
            
            # Collect race information
            race_info = {
                "event": f"{year} {gp} Grand Prix",
                "winner": None,
                "fastest_lap": None,
                "driver_data": [],
                "race_facts": []
            }
            
            # Get race winner
            results = session.results
            if not results.empty:
                winner = results.iloc[0]
                race_info["winner"] = f"{winner['Abbreviation']} ({winner['FullName']})"
                race_info["race_facts"].append(f"Winner: {winner['FullName']} ({winner['Abbreviation']})")
            
            # Get fastest lap
            fastest = session.laps.pick_fastest()
            if not fastest.empty:
                race_info["fastest_lap"] = {
                    "driver": fastest['Driver'],
                    "time": fastest['LapTime'].total_seconds(),
                    "lap": int(fastest['LapNumber'])
                }
                race_info["race_facts"].append(
                    f"Fastest lap: {fastest['Driver']} - {fastest['LapTime'].total_seconds():.3f}s"
                )
            
            # Get top driver data
            for idx, row in results.head(5).iterrows():
                driver_data = {
                    "position": row['Position'],
                    "driver": row['Abbreviation'],
                    "name": row['FullName'],
                    "team": row['TeamName']
                }
                race_info["driver_data"].append(driver_data)
                race_info["race_facts"].append(
                    f"{row['Position']}. {row['FullName']} ({row['Abbreviation']}) - {row['TeamName']}"
                )
            
            return race_info
            
        except Exception as e:
            print(f"Error loading {year} {gp}: {e}")
            return None
    
    def create_knowledge_texts(self) -> List[str]:
        """Convert F1 data into text documents for RAG"""
        texts = []
        
        # Get all available years from cache
        years = [2023, 2024, 2025, 2026]
        
        for year in years:
            try:
                schedule = fastf1.get_event_schedule(year)
                races = schedule[schedule['Session5'] == 'Race']
                
                for idx, race in races.head(10).iterrows():  # Limit to 10 races per year
                    gp_name = race['EventName']
                    print(f"Processing: {year} {gp_name}")
                    
                    data = self.extract_session_data(year, gp_name)
                    if data:
                        text = f"""
                        RACE: {data['event']}
                        WINNER: {data['winner']}
                        FASTEST LAP: Lap {data['fastest_lap']['lap'] if data['fastest_lap'] else 'N/A'} - {data['fastest_lap']['time']:.3f}s
                        TOP 5: {', '.join([f"{d['position']}. {d['driver']}" for d in data['driver_data']])}
                        """
                        texts.append(text.strip())
            except Exception as e:
                print(f"Error processing {year}: {e}")
                continue
        
        return texts
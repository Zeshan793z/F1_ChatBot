"""
Comparison Agent - Compares two drivers, teams, or seasons
Handles questions like "Compare Verstappen vs Hamilton", "Who was faster?", etc.
"""

import re
import fastf1
from pathlib import Path
import pandas as pd


class ComparisonAgent:
    def __init__(self):
        """Initialize the Comparison Agent"""
        print("⚖️ Initializing Comparison Agent...")
        
        # Setup FastF1 cache
        self.cache_dir = Path(__file__).parent.parent.parent / "data" / "fastf1_cache"
        fastf1.Cache.enable_cache(str(self.cache_dir))
        
        print("✅ Comparison Agent ready!")
    
    def compare(self, question: str) -> str:
        """
        Compare drivers, teams, or seasons based on the question
        
        Args:
            question: User's comparison question
        
        Returns:
            Comparison analysis
        """
        question_lower = question.lower()
        
        # Detect comparison type
        if self._is_driver_comparison(question_lower):
            return self._compare_drivers(question_lower)
        elif self._is_team_comparison(question_lower):
            return self._compare_teams(question_lower)
        elif self._is_season_comparison(question_lower):
            return self._compare_seasons(question_lower)
        elif self._is_race_comparison(question_lower):
            return self._compare_races(question_lower)
        else:
            return self._general_comparison(question_lower)
    
    def _is_driver_comparison(self, question_lower: str) -> bool:
        """Check if question compares two drivers"""
        # Look for patterns like "X vs Y", "compare X and Y", "X or Y"
        comparison_patterns = [
            r'(\w+)\s+vs\s+(\w+)',
            r'compare\s+(\w+)\s+and\s+(\w+)',
            r'(\w+)\s+or\s+(\w+)',
            r'(\w+)\s+versus\s+(\w+)'
        ]
        
        for pattern in comparison_patterns:
            match = re.search(pattern, question_lower, re.IGNORECASE)
            if match:
                return True
        return False
    
    def _is_team_comparison(self, question_lower: str) -> bool:
        """Check if question compares two teams"""
        teams = ['ferrari', 'mercedes', 'red bull', 'mclaren', 'aston martin', 'williams']
        team_count = sum(1 for team in teams if team in question_lower)
        return team_count >= 2
    
    def _is_season_comparison(self, question_lower: str) -> bool:
        """Check if question compares two seasons"""
        seasons = re.findall(r'20(2[3-6])', question_lower)
        return len(seasons) >= 2
    
    def _is_race_comparison(self, question_lower: str) -> bool:
        """Check if question compares two races"""
        races = ['miami', 'monaco', 'silverstone', 'spa', 'monza', 'singapore', 'abu dhabi']
        race_count = sum(1 for race in races if race in question_lower)
        return race_count >= 2
    
    def _extract_drivers(self, question_lower: str) -> tuple:
        """Extract two driver codes from the question"""
        driver_map = {
            'verstappen': 'VER', 'max': 'VER',
            'hamilton': 'HAM', 'lewis': 'HAM',
            'leclerc': 'LEC', 'charles': 'LEC',
            'norris': 'NOR', 'lando': 'NOR',
            'russell': 'RUS', 'george': 'RUS',
            'piastri': 'PIA', 'oscar': 'PIA',
            'sainz': 'SAI', 'carlos': 'SAI',
            'perez': 'PER', 'checo': 'PER',
            'alonso': 'ALO', 'fernando': 'ALO',
            'antonelli': 'ANT', 'kimi': 'ANT'
        }
        
        driver_names = []
        for name, code in driver_map.items():
            if name in question_lower:
                driver_names.append((name, code))
        
        # Take first two drivers found
        if len(driver_names) >= 2:
            return driver_names[0][1], driver_names[1][1]
        
        return None, None
    
    def _extract_year_and_gp(self, question_lower: str) -> tuple:
        """Extract year and GP from question"""
        year_match = re.search(r'20(2[3-6])', question_lower)
        year = int(year_match.group(0)) if year_match else 2026
        
        gp_list = ['miami', 'monaco', 'canadian', 'british', 'austrian', 
                   'belgian', 'italian', 'singapore', 'abu dhabi']
        
        gp = None
        for gp_name in gp_list:
            if gp_name in question_lower:
                gp = gp_name.capitalize() + " Grand Prix"
                break
        
        return year, gp
    
    def _compare_drivers(self, question_lower: str) -> str:
        """Compare two drivers"""
        driver1, driver2 = self._extract_drivers(question_lower)
        year, gp = self._extract_year_and_gp(question_lower)
        
        if not driver1 or not driver2:
            return "Please specify two drivers to compare. Example: 'Compare Verstappen and Hamilton in Canadian GP 2026'"
        
        print(f"⚖️ Comparing {driver1} vs {driver2} at {gp or 'unknown race'} {year}")
        
        # Fetch data for both drivers
        data1 = self._fetch_driver_data(year, gp, driver1)
        data2 = self._fetch_driver_data(year, gp, driver2)
        
        if not data1 or not data2:
            return f"Could not find data for {driver1} or {driver2} at {gp} {year}. Make sure the race has occurred."
        
        # Generate comparison
        return self._generate_driver_comparison(driver1, driver2, data1, data2, gp, year)
    
    def _fetch_driver_data(self, year: int, gp: str, driver_code: str) -> dict:
        """Fetch driver data from FastF1"""
        try:
            if not gp:
                return None
            
            session = fastf1.get_session(year, gp, "R")
            session.load(telemetry=False, laps=True, weather=False)
            
            driver_laps = session.laps.pick_driver(driver_code)
            if driver_laps.empty:
                return None
            
            results = session.results
            driver_result = results[results['Abbreviation'] == driver_code]
            
            # Get fastest lap
            fastest = driver_laps.pick_fastest()
            fastest_time = fastest['LapTime'].total_seconds() if fastest is not None else None
            
            # Get average lap time
            lap_times = driver_laps['LapTime'].dropna()
            avg_lap = lap_times.dt.total_seconds().mean() if not lap_times.empty else None
            
            # Get finishing position
            finish_pos = None
            start_pos = None
            if not driver_result.empty:
                finish_pos = int(driver_result['Position'].values[0])
                start_pos = int(driver_result['GridPosition'].values[0])
            
            # Get pit stops
            pit_stops = driver_laps.dropna(subset=['PitInTime'])
            pit_count = len(pit_stops)
            
            return {
                'driver': driver_code,
                'start_pos': start_pos,
                'finish_pos': finish_pos,
                'fastest_lap': fastest_time,
                'avg_lap': avg_lap,
                'pit_stops': pit_count,
                'laps_completed': len(driver_laps)
            }
            
        except Exception as e:
            print(f"Error fetching data for {driver_code}: {e}")
            return None
    
    def _generate_driver_comparison(self, driver1: str, driver2: str, data1: dict, data2: dict, gp: str, year: int) -> str:
        """Generate a readable driver comparison"""
        
        driver_names = {
            'VER': 'Verstappen', 'HAM': 'Hamilton', 'LEC': 'Leclerc',
            'NOR': 'Norris', 'RUS': 'Russell', 'PIA': 'Piastri',
            'SAI': 'Sainz', 'PER': 'Perez', 'ALO': 'Alonso', 'ANT': 'Antonelli'
        }
        name1 = driver_names.get(driver1, driver1)
        name2 = driver_names.get(driver2, driver2)
        
        comparison = f"📊 **Comparison: {name1} vs {name2} at {gp} {year}**\n\n"
        
        # Starting positions
        comparison += f"**Starting Positions:**\n"
        comparison += f"  • {name1}: P{data1['start_pos']}\n"
        comparison += f"  • {name2}: P{data2['start_pos']}\n\n"
        
        # Finishing positions
        comparison += f"**Finishing Positions:**\n"
        comparison += f"  • {name1}: P{data1['finish_pos']}\n"
        comparison += f"  • {name2}: P{data2['finish_pos']}\n"
        
        # Who finished ahead
        if data1['finish_pos'] < data2['finish_pos']:
            comparison += f"  → {name1} finished ahead of {name2}\n\n"
        elif data2['finish_pos'] < data1['finish_pos']:
            comparison += f"  → {name2} finished ahead of {name1}\n\n"
        else:
            comparison += f"  → Both drivers finished in the same position\n\n"
        
        # Fastest lap comparison
        comparison += f"**Fastest Lap:**\n"
        comparison += f"  • {name1}: {data1['fastest_lap']:.3f}s\n"
        comparison += f"  • {name2}: {data2['fastest_lap']:.3f}s\n"
        
        if data1['fastest_lap'] < data2['fastest_lap']:
            diff = data2['fastest_lap'] - data1['fastest_lap']
            comparison += f"  → {name1} was {diff:.3f}s faster\n\n"
        else:
            diff = data1['fastest_lap'] - data2['fastest_lap']
            comparison += f"  → {name2} was {diff:.3f}s faster\n\n"
        
        # Pit stops
        comparison += f"**Pit Stops:**\n"
        comparison += f"  • {name1}: {data1['pit_stops']} stops\n"
        comparison += f"  • {name2}: {data2['pit_stops']} stops\n\n"
        
        # Average lap time (consistency)
        if data1['avg_lap'] and data2['avg_lap']:
            comparison += f"**Average Lap Time (Consistency):**\n"
            comparison += f"  • {name1}: {data1['avg_lap']:.3f}s\n"
            comparison += f"  • {name2}: {data2['avg_lap']:.3f}s\n"
            
            if data1['avg_lap'] < data2['avg_lap']:
                diff = data2['avg_lap'] - data1['avg_lap']
                comparison += f"  → {name1} was more consistent ({diff:.3f}s faster on average)\n"
            else:
                diff = data1['avg_lap'] - data2['avg_lap']
                comparison += f"  → {name2} was more consistent ({diff:.3f}s faster on average)\n"
        
        return comparison
    
    def _compare_teams(self, question_lower: str) -> str:
        """Compare two teams"""
        return "🔜 Team comparison coming soon! For now, try comparing specific drivers."
    
    def _compare_seasons(self, question_lower: str) -> str:
        """Compare two seasons"""
        return "🔜 Season comparison coming soon! For now, try comparing drivers in a specific race."
    
    def _compare_races(self, question_lower: str) -> str:
        """Compare two races"""
        return "🔜 Race comparison coming soon! For now, try comparing drivers."
    
    def _general_comparison(self, question_lower: str) -> str:
        """Handle general comparison questions"""
        return """I can help you compare drivers! Try asking:

• "Compare Verstappen and Hamilton in Canadian GP 2026"
• "Who was faster, Norris or Piastri in Miami 2026?"
• "Verstappen vs Leclerc at Monaco 2026"

Please specify two drivers and a race."""
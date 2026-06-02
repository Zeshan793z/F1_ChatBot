"""
Strategy Agent - Explains WHY strategic decisions were made
Handles questions about pit stops, tire choices, race strategy, etc.
"""

import re
import fastf1
from pathlib import Path
from .rag_agent import F1RAGAgent


class StrategyAgent:
    def __init__(self):
        """Initialize the Strategy Agent"""
        print("🎯 Initializing Strategy Agent...")
        self.data_agent = F1RAGAgent()
        self.data_agent.initialize_knowledge_base(force_reload=False)
        
        # Setup FastF1 cache
        self.cache_dir = Path(__file__).parent.parent.parent / "data" / "fastf1_cache"
        fastf1.Cache.enable_cache(str(self.cache_dir))
        
        print("✅ Strategy Agent ready!")
    
    def analyze(self, question: str) -> str:
        """Analyze and explain strategic decisions"""
        question_lower = question.lower()
        
        # Extract driver, year, gp
        driver, year, gp = self._extract_context(question_lower)
        
        print(f"🔍 Extracted - Driver: {driver}, Year: {year}, GP: {gp}")
        
        if not driver or not year or not gp:
            return self._help_refine_question(question, driver, year, gp)
        
        # Fetch actual strategy data from FastF1
        strategy_data = self._fetch_strategy_from_fastf1(year, gp, driver)
        
        if strategy_data:
            return self._format_strategy_answer(driver, gp, year, strategy_data)
        
        return f"I couldn't find strategy data for {driver} at the {gp} {year}."
    
    def _extract_context(self, question_lower: str) -> tuple:
        """Extract driver code, year, and GP from question"""
        driver = None
        year = None
        gp = None
        
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
        
        for name, code in driver_map.items():
            if name in question_lower:
                driver = code
                break
        
        year_match = re.search(r'20(2[3-6])', question_lower)
        if year_match:
            year = int(year_match.group(0))
        
        gp_list = ['canadian', 'miami', 'australian', 'chinese', 'japanese',
                   'monaco', 'british', 'austrian', 'belgian', 'italian']
        
        for gp_name in gp_list:
            if gp_name in question_lower:
                gp = gp_name.capitalize() + " Grand Prix"
                break
        
        return driver, year, gp
    
    def _fetch_strategy_from_fastf1(self, year: int, gp: str, driver_code: str) -> dict:
        """Fetch strategy data directly from FastF1 cache"""
        try:
            print(f"📊 Fetching FastF1 data for {year} {gp} - {driver_code}")
            session = fastf1.get_session(year, gp, "R")
            session.load(telemetry=False, laps=True, weather=False)
            
            # Get driver laps
            driver_laps = session.laps.pick_driver(driver_code)
            
            if driver_laps.empty:
                print(f"⚠️ No laps found for {driver_code}")
                return None
            
            # Get results
            results = session.results
            driver_result = results[results['Abbreviation'] == driver_code]
            
            # Extract data
            strategy_data = {
                'starting_pos': None,
                'finishing_pos': None,
                'tires_used': [],
                'pit_stops': [],
                'fastest_lap': None,
                'fastest_lap_time': None,
                'avg_lap_time': None
            }
            
            # Starting and finishing positions
            if not driver_result.empty:
                strategy_data['starting_pos'] = int(driver_result['GridPosition'].values[0])
                strategy_data['finishing_pos'] = int(driver_result['Position'].values[0])
            
            # Tires used
            strategy_data['tires_used'] = list(driver_laps['Compound'].unique())
            
            # Pit stops
            pit_stops = driver_laps.dropna(subset=['PitInTime'])
            strategy_data['pit_stops'] = [int(lap) for lap in pit_stops['LapNumber'].values]
            
            # Fastest lap
            fastest = driver_laps.pick_fastest()
            if fastest is not None:
                strategy_data['fastest_lap'] = int(fastest['LapNumber'])
                strategy_data['fastest_lap_time'] = fastest['LapTime'].total_seconds()
            
            # Average lap time
            lap_times = driver_laps['LapTime'].dropna()
            if not lap_times.empty:
                strategy_data['avg_lap_time'] = lap_times.dt.total_seconds().mean()
            
            print(f"✅ Found strategy data: P{strategy_data['starting_pos']} → P{strategy_data['finishing_pos']}, {len(strategy_data['pit_stops'])} stops")
            return strategy_data
            
        except Exception as e:
            print(f"❌ Error fetching FastF1 data: {e}")
            return None
    
    def _format_strategy_answer(self, driver_code: str, gp: str, year: int, data: dict) -> str:
        """Format the strategy data into a readable answer"""
        
        # Map driver codes to names
        driver_names = {
            'VER': 'Verstappen', 'HAM': 'Hamilton', 'LEC': 'Leclerc',
            'NOR': 'Norris', 'RUS': 'Russell', 'PIA': 'Piastri',
            'SAI': 'Sainz', 'PER': 'Perez', 'ALO': 'Alonso', 'ANT': 'Antonelli'
        }
        driver_name = driver_names.get(driver_code, driver_code)
        
        # Build answer
        answer = f"{driver_name} started from P{data['starting_pos']} at the {year} {gp}. "
        
        # Tire strategy
        if data['tires_used']:
            tires = ' → '.join(data['tires_used'])
            answer += f"He used a {len(data['tires_used'])}-compound strategy: {tires}. "
        
        # Pit stops
        if data['pit_stops']:
            if len(data['pit_stops']) == 1:
                answer += f"He made a single pit stop on lap {data['pit_stops'][0]}. "
            else:
                answer += f"He made {len(data['pit_stops'])} pit stops on laps {', '.join(map(str, data['pit_stops']))}. "
        
        # Result
        answer += f"He finished in P{data['finishing_pos']}. "
        
        # Fastest lap
        if data['fastest_lap']:
            answer += f"His fastest lap was {data['fastest_lap_time']:.3f}s on lap {data['fastest_lap']}."
        
        return answer
    
    def _help_refine_question(self, question: str, driver: str, year: int, gp: str) -> str:
        """Help user refine their question"""
        missing = []
        if not driver:
            missing.append("driver")
        if not year:
            missing.append("year")
        if not gp:
            missing.append("Grand Prix")
        
        if missing:
            return f"Please include the {', '.join(missing)} in your question.\n\nExample: 'What was Verstappen's strategy in Canadian GP 2026?'"
        
        return f"I couldn't find strategy data for that specific query. Try asking about a known race like 'Canadian GP 2026'."


# For backwards compatibility
def explain_strategy(data: str, question: str) -> str:
    agent = StrategyAgent()
    return agent.analyze(question)
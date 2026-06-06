"""
Strategy Agent - Explains WHY strategic decisions were made
Handles questions about pit stops, tire choices, race strategy, Includes weather strategy analysis etc.
"""

import re
import fastf1
from pathlib import Path
import pandas as pd
from datetime import datetime


class StrategyAgent:
    def __init__(self):
        """Initialize the Strategy Agent"""
        print("🎯 Initializing Strategy Agent...")
        
        # Setup FastF1 cache
        self.cache_dir = Path(__file__).parent.parent.parent / "data" / "fastf1_cache"
        fastf1.Cache.enable_cache(str(self.cache_dir))
        
        print("✅ Strategy Agent ready!")
    
    def analyze(self, question: str) -> str:
        """Analyze and explain strategic decisions"""
        question_lower = question.lower()
        
        print(f"\n🔍 Analyzing question: {question}")
        
        # Check for weather-specific questions
        if self._is_weather_question(question_lower):
            print("🌤️ Weather question detected")
            return self._weather_strategy_analysis(question_lower)
        
        # Extract driver, year, gp
        driver, year, gp = self._extract_context(question_lower)
        
        print(f"🔍 Extracted - Driver: {driver}, Year: {year}, GP: {gp}")
        
        if not driver or not year or not gp:
            return self._help_refine_question(question, driver, year, gp)
        
        # Fetch strategy data including weather
        strategy_data = self._fetch_strategy_with_weather(year, gp, driver)
        
        if strategy_data:
            # Check if weather played a role
            if self._weather_affected_race(strategy_data):
                return self._format_weather_strategy_answer(driver, gp, year, strategy_data)
            return self._format_strategy_answer(driver, gp, year, strategy_data)
        
        return f"I couldn't find strategy data for {driver} at the {gp} {year}."
    
    def _is_weather_question(self, question_lower: str) -> bool:
        """Check if question is about weather strategy"""
        weather_keywords = [
            'weather', 'rain', 'wet', 'dry', 'temperature', 'humidity',
            'conditions', 'forecast', 'storm', 'cloud', 'sunny', 'overcast',
            'how was the weather', 'weather like', 'climate', 'temp',
            'air temp', 'track temp', 'rainfall', 'wind'
        ]
        return any(keyword in question_lower for keyword in weather_keywords)
    
    def _weather_strategy_analysis(self, question_lower: str) -> str:
        """Provide weather-specific strategy analysis"""
        
        # Extract race context
        year, gp, driver = self._extract_weather_context(question_lower)
        
        print(f"  Extracted - Year: {year}, GP: {gp}, Driver: {driver}")
        
        if not year or not gp:
            print("  Missing year or GP, returning help")
            return self._weather_help()
        
        # Fetch weather data
        weather_data = self._fetch_weather_data(year, gp)
        
        if not weather_data:
            return f"I couldn't find weather data for {gp} {year}. The race may not have occurred yet or weather data isn't available."
        
        # Fetch race results to see how weather affected outcomes
        results = self._fetch_race_results_with_weather(year, gp)
        
        # Generate weather strategy analysis
        return self._generate_weather_analysis(weather_data, results, gp, year, driver)
    
    def _extract_weather_context(self, question_lower: str) -> tuple:
        """Extract year, GP, and driver from weather question"""
        print(f"  Extracting weather context from: {question_lower}")
        
        year_match = re.search(r'20(2[3-6])', question_lower)
        year = int(year_match.group(0)) if year_match else None
        print(f"  Year found: {year}")
        
        gp_list = ['miami', 'monaco', 'canadian', 'british', 'austrian', 
                   'belgian', 'italian', 'singapore', 'abu dhabi', 'dutch',
                   'spanish', 'hungarian', 'mexico', 'brazil', 'australian',
                   'chinese', 'japanese']
        
        gp = None
        for gp_name in gp_list:
            if gp_name in question_lower:
                gp = gp_name.capitalize() + " Grand Prix"
                print(f"  GP found: {gp}")
                break
        
        if not gp:
            print("  No GP found in question")
        
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
        
        driver = None
        for name, code in driver_map.items():
            if name in question_lower:
                driver = code
                print(f"  Driver found: {driver}")
                break
        
        return year, gp, driver
    
    def _fetch_weather_data(self, year: int, gp: str) -> dict:
        """Fetch weather data for a race"""
        try:
            print(f"🌤️ Fetching weather data for {year} {gp}...")
            
            session = fastf1.get_session(year, gp, "R")
            # Load with weather=True to get weather data
            session.load(telemetry=False, laps=False, weather=True)
            
            # Check if weather_data exists
            if not hasattr(session, 'weather_data') or session.weather_data is None:
                print("⚠️ No weather_data attribute in session")
                return None
            
            weather = session.weather_data
            
            if weather.empty:
                print("⚠️ Weather data is empty")
                return None
            
            print(f"✅ Weather data loaded: {len(weather)} records")
            
            weather_info = {
                'air_temp': None,
                'track_temp': None,
                'humidity': None,
                'rainfall': None,
                'pressure': None,
                'wind_speed': None,
                'conditions': []
            }
            
            # Extract data - using proper pandas Series access
            if 'AirTemp' in weather.columns:
                # Convert to numeric and handle any NaN values
                air_temp_series = pd.to_numeric(weather['AirTemp'], errors='coerce')
                weather_info['air_temp'] = air_temp_series.mean()
                print(f"  AirTemp: {weather_info['air_temp']:.1f}°C")
            
            if 'TrackTemp' in weather.columns:
                track_temp_series = pd.to_numeric(weather['TrackTemp'], errors='coerce')
                weather_info['track_temp'] = track_temp_series.mean()
                print(f"  TrackTemp: {weather_info['track_temp']:.1f}°C")
            
            if 'Humidity' in weather.columns:
                humidity_series = pd.to_numeric(weather['Humidity'], errors='coerce')
                weather_info['humidity'] = humidity_series.mean()
                print(f"  Humidity: {weather_info['humidity']:.1f}%")
            
            if 'Rainfall' in weather.columns:
                rainfall_series = pd.to_numeric(weather['Rainfall'], errors='coerce')
                weather_info['rainfall'] = rainfall_series.mean()
                print(f"  Rainfall: {weather_info['rainfall']:.2f}mm")
            
            if 'Pressure' in weather.columns:
                pressure_series = pd.to_numeric(weather['Pressure'], errors='coerce')
                weather_info['pressure'] = pressure_series.mean()
            
            if 'WindSpeed' in weather.columns:
                wind_series = pd.to_numeric(weather['WindSpeed'], errors='coerce')
                weather_info['wind_speed'] = wind_series.mean()
            
            # Determine conditions
            if weather_info['rainfall'] and weather_info['rainfall'] > 0:
                weather_info['conditions'].append("🌧️ Rain")
            if weather_info['air_temp']:
                if weather_info['air_temp'] > 30:
                    weather_info['conditions'].append("🔥 Hot")
                elif weather_info['air_temp'] < 15:
                    weather_info['conditions'].append("❄️ Cool")
                else:
                    weather_info['conditions'].append("🌡️ Mild")
            
            if not weather_info['conditions']:
                weather_info['conditions'].append("☀️ Dry")
            
            return weather_info
            
        except Exception as e:
            print(f"❌ Error fetching weather data: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _fetch_race_results_with_weather(self, year: int, gp: str) -> dict:
        """Fetch race results to see weather impact"""
        try:
            session = fastf1.get_session(year, gp, "R")
            session.load(telemetry=False, laps=True, weather=False)
            
            results = session.results
            fastest = session.laps.pick_fastest()
            
            return {
                'winner': results.iloc[0]['Abbreviation'] if not results.empty else None,
                'fastest_lap_driver': fastest['Driver'] if fastest is not None else None,
                'total_drivers': len(results)
            }
            
        except Exception as e:
            print(f"Error fetching results: {e}")
            return None
    
    def _generate_weather_analysis(self, weather: dict, results: dict, gp: str, year: int, driver: str = None) -> str:
        """Generate weather strategy analysis"""
        
        analysis = f"🌤️ **Weather Analysis for {gp} {year}**\n\n"
        
        # Weather conditions
        analysis += "**Race Conditions:**\n"
        if weather['air_temp']:
            analysis += f"  • Air Temperature: {weather['air_temp']:.1f}°C\n"
        if weather['track_temp']:
            analysis += f"  • Track Temperature: {weather['track_temp']:.1f}°C\n"
        if weather['humidity']:
            analysis += f"  • Humidity: {weather['humidity']:.1f}%\n"
        if weather['rainfall'] and weather['rainfall'] > 0:
            analysis += f"  • Rainfall: {weather['rainfall']:.1f}mm\n"
        if weather['wind_speed']:
            analysis += f"  • Wind Speed: {weather['wind_speed']:.1f} km/h\n"
        
        analysis += f"  • Overall: {', '.join(weather['conditions'])}\n\n"
        
        # Strategy recommendations based on weather
        analysis += "**Weather Strategy Insights:**\n"
        
        if weather['rainfall'] and weather['rainfall'] > 0:
            analysis += "  • 🌧️ **Wet Race Conditions**\n"
            analysis += "    - Teams should consider intermediate or wet tires\n"
            analysis += "    - Expect more pit stops and safety cars\n"
            analysis += "    - Drivers who excel in wet conditions have advantage\n"
        elif weather['air_temp'] and weather['air_temp'] > 30:
            analysis += "  • 🔥 **Hot Conditions**\n"
            analysis += "    - High tire degradation expected\n"
            analysis += "    - Engine cooling becomes critical\n"
            analysis += "    - Drivers need to manage tire temperatures\n"
        elif weather['air_temp'] and weather['air_temp'] < 15:
            analysis += "  • ❄️ **Cool Conditions**\n"
            analysis += "    - Tire warm-up may be difficult\n"
            analysis += "    - Extra lap to reach optimal tire temperature\n"
            analysis += "    - Risk of losing tire temperature during safety car\n"
        
        if weather['track_temp'] and weather['air_temp']:
            temp_diff = weather['track_temp'] - weather['air_temp']
            if temp_diff > 15:
                analysis += f"\n  • 🔆 **High Track Temperature** (Track {temp_diff:.0f}°C hotter than air)\n"
                analysis += "    - High tire wear, graining possible\n"
                analysis += "    - Multiple pit stop strategy likely\n"
            elif temp_diff < 5:
                analysis += f"\n  • ❄️ **Low Track Temperature** (Track only {temp_diff:.0f}°C above air)\n"
                analysis += "    - Difficult to get tires in operating window\n"
                analysis += "    - Extra formation lap may help\n"
        
        # Race outcome if available
        if results and results.get('winner'):
            analysis += f"\n**Race Outcome:**\n"
            analysis += f"  • Winner: {results['winner']}\n"
            if results.get('fastest_lap_driver'):
                analysis += f"  • Fastest Lap: {results['fastest_lap_driver']}\n"
        
        # Driver-specific advice
        if driver:
            driver_names = {
                'VER': 'Verstappen', 'HAM': 'Hamilton', 'LEC': 'Leclerc',
                'NOR': 'Norris', 'RUS': 'Russell', 'PIA': 'Piastri',
                'SAI': 'Sainz', 'PER': 'Perez', 'ALO': 'Alonso', 'ANT': 'Antonelli'
            }
            driver_name = driver_names.get(driver, driver)
            analysis += f"\n**Advice for {driver_name}:**\n"
            if weather['rainfall'] and weather['rainfall'] > 0:
                analysis += "  • Focus on staying on track and avoiding incidents\n"
                analysis += "  • Wet weather specialists gain positions in rain\n"
            elif weather['air_temp'] and weather['air_temp'] > 30:
                analysis += "  • Tire management is key - avoid aggressive pushing early\n"
                analysis += "  • Consider an extra pit stop for fresh tires\n"
            elif weather['air_temp'] and weather['air_temp'] < 15:
                analysis += "  • Take extra care on out-laps to warm tires\n"
                analysis += "  • Be aggressive on first lap to gain positions\n"
            else:
                analysis += "  • Normal race strategy applies\n"
                analysis += "  • Focus on qualifying position\n"
        
        return analysis
    
    def _weather_help(self) -> str:
        """Provide help for weather questions"""
        return """🌤️ **Weather Strategy Questions**

You can ask about weather strategy like:

• "What was the weather like in Canadian GP 2026?"
• "How did rain affect the Monaco GP?"
• "Weather strategy for Miami GP"
• "What tires should be used in wet conditions?"

I'll analyze temperature, humidity, rainfall, and provide strategy recommendations!"""
    
    def _fetch_strategy_with_weather(self, year: int, gp: str, driver_code: str) -> dict:
        """Fetch strategy data including weather"""
        try:
            session = fastf1.get_session(year, gp, "R")
            session.load(telemetry=False, laps=True, weather=True)
            
            driver_laps = session.laps.pick_driver(driver_code)
            if driver_laps.empty:
                return None
            
            results = session.results
            driver_result = results[results['Abbreviation'] == driver_code]
            
            # Extract weather data
            weather_info = {}
            if hasattr(session, 'weather_data') and session.weather_data is not None:
                weather = session.weather_data
                if 'AirTemp' in weather.columns:
                    weather_info['air_temp'] = weather['AirTemp'].mean()
                if 'TrackTemp' in weather.columns:
                    weather_info['track_temp'] = weather['TrackTemp'].mean()
                if 'Rainfall' in weather.columns:
                    weather_info['rainfall'] = weather['Rainfall'].mean()
            
            # Extract race data
            fastest = driver_laps.pick_fastest()
            
            strategy_data = {
                'driver': driver_code,
                'starting_pos': int(driver_result['GridPosition'].values[0]) if not driver_result.empty else None,
                'finishing_pos': int(driver_result['Position'].values[0]) if not driver_result.empty else None,
                'tires_used': list(driver_laps['Compound'].unique()),
                'pit_stops': [int(lap) for lap in driver_laps.dropna(subset=['PitInTime'])['LapNumber'].values],
                'fastest_lap': fastest['LapTime'].total_seconds() if fastest is not None else None,
                'fastest_lap_num': int(fastest['LapNumber']) if fastest is not None else None,
                'weather': weather_info
            }
            
            return strategy_data
            
        except Exception as e:
            print(f"Error fetching strategy data: {e}")
            return None
    
    def _weather_affected_race(self, data: dict) -> bool:
        """Determine if weather affected the race"""
        weather = data.get('weather', {})
        return weather.get('rainfall', 0) > 0 or weather.get('air_temp', 20) > 35 or weather.get('air_temp', 20) < 10
    
    def _format_weather_strategy_answer(self, driver_code: str, gp: str, year: int, data: dict) -> str:
        """Format strategy answer with weather context"""
        
        driver_names = {
            'VER': 'Verstappen', 'HAM': 'Hamilton', 'LEC': 'Leclerc',
            'NOR': 'Norris', 'RUS': 'Russell', 'PIA': 'Piastri',
            'SAI': 'Sainz', 'PER': 'Perez', 'ALO': 'Alonso', 'ANT': 'Antonelli'
        }
        driver_name = driver_names.get(driver_code, driver_code)
        
        weather = data.get('weather', {})
        
        answer = f"🏁 **{driver_name}'s Strategy at {gp} {year}**\n\n"
        
        # Weather conditions
        answer += "**Weather Conditions:**\n"
        if weather.get('air_temp'):
            answer += f"  • Air Temperature: {weather['air_temp']:.0f}°C\n"
        if weather.get('track_temp'):
            answer += f"  • Track Temperature: {weather['track_temp']:.0f}°C\n"
        if weather.get('rainfall', 0) > 0:
            answer += f"  • Rainfall: {weather['rainfall']:.1f}mm - Wet race conditions\n"
        else:
            answer += "  • Dry race conditions\n"
        
        answer += "\n**Race Strategy:**\n"
        answer += f"  • Started: P{data['starting_pos']}\n"
        answer += f"  • Finished: P{data['finishing_pos']}\n"
        answer += f"  • Tires Used: {' → '.join(data['tires_used'])}\n"
        answer += f"  • Pit Stops: {len(data['pit_stops'])} stops on laps {', '.join(map(str, data['pit_stops']))}\n"
        
        if data['fastest_lap']:
            answer += f"  • Fastest Lap: {data['fastest_lap']:.3f}s (Lap {data['fastest_lap_num']})\n"
        
        # Weather impact on strategy
        answer += "\n**Weather Impact on Strategy:**\n"
        if weather.get('rainfall', 0) > 0:
            answer += "  • Wet conditions required intermediate or wet tires\n"
            answer += "  • Teams had to time the switch to dry tires carefully\n"
            answer += "  • Safety cars likely due to reduced visibility\n"
        elif weather.get('air_temp', 20) > 32:
            answer += "  • High temperatures caused increased tire degradation\n"
            answer += "  • Drivers had to manage tire temperatures carefully\n"
            answer += "  • Teams considered 2-stop vs 3-stop strategies\n"
        elif weather.get('air_temp', 20) < 12:
            answer += "  • Cool conditions made tire warm-up difficult\n"
            answer += "  • Drivers needed extra laps to reach optimal temperatures\n"
            answer += "  • Risk of losing tire temperature during safety car\n"
        
        return answer
    
    def _format_strategy_answer(self, driver_code: str, gp: str, year: int, data: dict) -> str:
        """Format the strategy data into a readable answer (no weather)"""
        
        driver_names = {
            'VER': 'Verstappen', 'HAM': 'Hamilton', 'LEC': 'Leclerc',
            'NOR': 'Norris', 'RUS': 'Russell', 'PIA': 'Piastri',
            'SAI': 'Sainz', 'PER': 'Perez', 'ALO': 'Alonso', 'ANT': 'Antonelli'
        }
        driver_name = driver_names.get(driver_code, driver_code)
        
        answer = f"**{driver_name}'s Strategy at {gp} {year}**\n\n"
        answer += f"  • Started: P{data['starting_pos']}\n"
        answer += f"  • Finished: P{data['finishing_pos']}\n"
        answer += f"  • Tires Used: {' → '.join(data['tires_used'])}\n"
        answer += f"  • Pit Stops: {len(data['pit_stops'])} stops on laps {', '.join(map(str, data['pit_stops']))}\n"
        
        if data['fastest_lap']:
            answer += f"  • Fastest Lap: {data['fastest_lap']:.3f}s (Lap {data['fastest_lap_num']})\n"
        
        return answer
    
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
        
        gp_list = ['miami', 'monaco', 'canadian', 'british', 'austrian', 
                   'belgian', 'italian', 'singapore', 'abu dhabi', 'dutch',
                   'spanish', 'hungarian', 'mexico', 'brazil']
        
        for gp_name in gp_list:
            if gp_name in question_lower:
                gp = gp_name.capitalize() + " Grand Prix"
                break
        
        return driver, year, gp
    
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
            return f"Please include the {', '.join(missing)} in your question.\n\nExample: 'What was Verstappen's strategy in Canadian GP 2026?'\n\nOr ask about weather: 'What was the weather like in Canadian GP 2026?'"
        
        return f"I couldn't find strategy data for that specific query. Try asking about a known race like 'Canadian GP 2026'."


# For backwards compatibility
def explain_strategy(data: str, question: str) -> str:
    agent = StrategyAgent()
    return agent.analyze(question)
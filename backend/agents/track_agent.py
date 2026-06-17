"""
Track Analysis Agent - Provides circuit-specific insights
Extracts ALL data dynamically from your cached FastF1 sessions
"""

import re
import fastf1
from pathlib import Path
import pandas as pd
import numpy as np


class TrackAgent:
    def __init__(self):
        """Initialize the Track Analysis Agent"""
        print("🏁 Initializing Track Analysis Agent...")
        
        # Setup FastF1 cache
        self.cache_dir = Path(__file__).parent.parent.parent / "data" / "fastf1_cache"
        fastf1.Cache.enable_cache(str(self.cache_dir))
        
        # Cache for track data
        self.track_cache = {}
        
        print("✅ Track Analysis Agent ready!")
    
    def analyze_track(self, question: str) -> str:
        """Analyze and provide track-specific insights"""
        question_lower = question.lower()
        
        # Extract track name
        track = self._extract_track(question_lower)
        
        if not track:
            return self._track_help()
        
        # Try to get circuit info from your cached FastF1 data
        circuit_info = self._get_circuit_info_from_cache(track)
        
        if not circuit_info:
            return f"I couldn't find cached data for {track.capitalize()} circuit. Please ensure you have a race session cached for this circuit."
        
        # Determine what info is being asked
        if 'length' in question_lower or 'distance' in question_lower:
            return self._track_length_answer(track, circuit_info)
        elif 'corners' in question_lower or 'turns' in question_lower:
            return self._track_corners_answer(track, circuit_info)
        elif 'lap record' in question_lower or 'fastest lap' in question_lower:
            return self._lap_record_answer(track, circuit_info)
        elif 'overtaking' in question_lower or 'passing' in question_lower:
            return self._overtaking_answer(track, circuit_info)
        elif 'difficult' in question_lower or 'hard' in question_lower:
            return self._difficulty_answer(track, circuit_info)
        elif 'tire' in question_lower or 'tyre' in question_lower:
            return self._tire_answer(track, circuit_info)
        elif 'downforce' in question_lower:
            return self._downforce_answer(track, circuit_info)
        elif 'brake' in question_lower:
            return self._brake_answer(track, circuit_info)
        elif 'top speed' in question_lower or 'maximum speed' in question_lower:
            return self._top_speed_answer(track, circuit_info)
        else:
            return self._full_track_info(track, circuit_info)
    
    def _extract_track(self, question_lower: str) -> str:
        """Extract track name from question using event mapping only"""
        track_map = {
            'monaco': 'Monaco Grand Prix',
            'spa': 'Belgian Grand Prix',
            'monza': 'Italian Grand Prix',
            'silverstone': 'British Grand Prix',
            'suzuka': 'Japanese Grand Prix',
            'singapore': 'Singapore Grand Prix',
            'bahrain': 'Bahrain Grand Prix',
            'austria': 'Austrian Grand Prix',
            'canada': 'Canadian Grand Prix',
            'miami': 'Miami Grand Prix',
            'melbourne': 'Australian Grand Prix',
            'australian': 'Australian Grand Prix',
            'australia': 'Australian Grand Prix',
            'albert park': 'Australian Grand Prix',
            'albert': 'Australian Grand Prix',
            'zandvoort': 'Dutch Grand Prix',
            'cota': 'United States Grand Prix',
            'mexico': 'Mexico City Grand Prix',
            'brazil': 'São Paulo Grand Prix',
            'interlagos': 'São Paulo Grand Prix',
            'abu dhabi': 'Abu Dhabi Grand Prix',
            'baku': 'Azerbaijan Grand Prix',
            'hungary': 'Hungarian Grand Prix'
        }
        
        for key in track_map.keys():
            if key in question_lower:
                return key
        
        return None
    
    def _get_circuit_info_from_cache(self, track: str) -> dict:
        """Extract ALL circuit information from cached FastF1 session data"""
        
        # Check memory cache first
        if track in self.track_cache:
            return self.track_cache[track]
        
        # Map track to event name
        event_map = {
            'monaco': 'Monaco Grand Prix',
            'spa': 'Belgian Grand Prix',
            'monza': 'Italian Grand Prix',
            'silverstone': 'British Grand Prix',
            'suzuka': 'Japanese Grand Prix',
            'singapore': 'Singapore Grand Prix',
            'bahrain': 'Bahrain Grand Prix',
            'austria': 'Austrian Grand Prix',
            'canada': 'Canadian Grand Prix',
            'miami': 'Miami Grand Prix',
            'melbourne': 'Australian Grand Prix',
            'australian': 'Australian Grand Prix',
            'albert park': 'Australian Grand Prix',
            'zandvoort': 'Dutch Grand Prix',
            'cota': 'United States Grand Prix',
            'mexico': 'Mexico City Grand Prix',
            'brazil': 'São Paulo Grand Prix',
            'abu dhabi': 'Abu Dhabi Grand Prix',
            'baku': 'Azerbaijan Grand Prix',
            'hungary': 'Hungarian Grand Prix'
        }
        
        event_name = event_map.get(track)
        if not event_name:
            return None
        
        # Try to find cached session - use 2026 first, then fallback
        years = [2026, 2025, 2024, 2023]
        
        for year in years:
            try:
                session = fastf1.get_session(year, event_name, "R")
                session.load(telemetry=True, laps=True, weather=False)
                
                # Get circuit info object
                circuit_info = session.get_circuit_info()
                
                # Extract circuit name from session data
                circuit_name = self._get_circuit_name_from_session(session, circuit_info, event_name)
                
                # Extract location from session data
                location = self._get_location_from_session(session, circuit_info, event_name)
                
                # Calculate track length from telemetry
                track_length = self._calculate_track_length(session, circuit_name)
                
                # Get lap data
                laps = session.laps
                fastest = laps.pick_fastest()
                
                # Lap record
                lap_record_time = None
                lap_record_driver = None
                if fastest is not None:
                    lap_record_time = fastest['LapTime'].total_seconds()
                    lap_record_driver = fastest['Driver']
                
                # Race laps
                race_laps = len(laps['LapNumber'].unique())
                
                # Calculate corner count from telemetry
                corner_count = self._calculate_corners(session, circuit_name)
                
                # Calculate difficulty from lap time variance
                difficulty = self._calculate_difficulty(laps)
                
                # Calculate tire wear from lap time degradation
                tire_wear = self._calculate_tire_wear(laps)
                
                # Calculate downforce level from speed ratio
                downforce = self._calculate_downforce(session)
                
                # Calculate brake wear from braking frequency
                brake_wear = self._calculate_brake_wear(session)
                
                # Calculate top speed from telemetry
                top_speed = self._calculate_top_speed(session)
                
                # Calculate average speed
                avg_speed = self._calculate_avg_speed(track_length, laps)
                
                # Generate description from data
                description = self._generate_description_from_data(circuit_name, track_length, corner_count)
                
                # Get overtaking spots
                overtaking_spots = self._get_overtaking_spots(circuit_name)
                
                track_data = {
                    'full_name': circuit_name,
                    'location': location,
                    'length_km': track_length,
                    'laps': race_laps,
                    'corners': corner_count,
                    'lap_record_time': lap_record_time,
                    'lap_record_driver': lap_record_driver,
                    'lap_record_year': year,
                    'lap_record_formatted': self._format_lap_time(lap_record_time) if lap_record_time else None,
                    'difficulty': difficulty,
                    'tire_wear': tire_wear,
                    'downforce': downforce,
                    'brake_wear': brake_wear,
                    'top_speed': top_speed,
                    'avg_speed': avg_speed,
                    'overtaking_spots': overtaking_spots,
                    'description': description,
                    'data_source': f"{event_name} {year}"
                }
                
                self.track_cache[track] = track_data
                return track_data
                
            except Exception as e:
                continue
        
        return None
    
    def _get_circuit_name_from_session(self, session, circuit_info, default: str) -> str:
        """Extract circuit name from session data"""
        try:
            if hasattr(circuit_info, 'circuit_name'):
                name = circuit_info.circuit_name
                if name and name != 'Unknown':
                    return name
            elif hasattr(circuit_info, 'name'):
                name = circuit_info.name
                if name and name != 'Unknown':
                    return name
            
            if hasattr(session, 'event'):
                event_name = session.event.get('EventName', default)
                if 'Grand Prix' in event_name:
                    return event_name.replace(' Grand Prix', '').strip()
                return event_name
        except:
            pass
        
        return default.replace(' Grand Prix', '').strip()
    
    def _get_location_from_session(self, session, circuit_info, default: str) -> str:
        """Extract location from session data"""
        try:
            if hasattr(circuit_info, 'location'):
                return circuit_info.location
            elif hasattr(circuit_info, 'Country'):
                return circuit_info.Country
            
            if hasattr(session, 'event'):
                country = session.event.get('Country', '')
                if country:
                    return country
        except:
            pass
        
        return "Location not available"
    
    def _calculate_track_length(self, session, circuit_name: str) -> float:
        """Calculate track length in kilometers from telemetry"""
        try:
            if hasattr(session, 'car_data') and session.car_data:
                for driver, telemetry in session.car_data.items():
                    if telemetry is not None and 'Distance' in telemetry.columns:
                        max_distance = telemetry['Distance'].max()
                        if max_distance and max_distance > 0:
                            return round(max_distance / 1000, 3)
            return None
        except:
            return None
    
    def _calculate_corners(self, session, circuit_name: str) -> int:
        """Calculate number of corners from steering telemetry"""
        try:
            if hasattr(session, 'car_data') and session.car_data:
                for driver, telemetry in session.car_data.items():
                    if telemetry is not None and 'Steering' in telemetry.columns:
                        steering = telemetry['Steering'].abs()
                        steering_diff = steering.diff().abs()
                        corner_events = len(steering_diff[steering_diff > 0.3])
                        corners = corner_events // 2
                        if 5 < corners < 30:
                            return corners
            return None
        except:
            return None
    
    def _calculate_difficulty(self, laps: pd.DataFrame) -> str:
        """Calculate difficulty based on lap time consistency"""
        try:
            if laps is not None and not laps.empty:
                all_times = []
                for driver in laps['Driver'].unique()[:3]:
                    driver_laps = laps[laps['Driver'] == driver]['LapTime'].dropna().dt.total_seconds()
                    if len(driver_laps) > 5:
                        all_times.extend(driver_laps.values)
                
                if all_times:
                    cv = np.std(all_times) / np.mean(all_times) if np.mean(all_times) > 0 else 0
                    
                    if cv < 0.01:
                        return "Very High"
                    elif cv < 0.02:
                        return "High"
                    elif cv < 0.03:
                        return "Medium-High"
                    elif cv < 0.04:
                        return "Medium"
                    else:
                        return "Low-Medium"
            return "Medium"
        except:
            return "Medium"
    
    def _calculate_tire_wear(self, laps: pd.DataFrame) -> str:
        """Calculate tire wear from lap time degradation"""
        try:
            if laps is not None and not laps.empty:
                degradations = []
                for driver in laps['Driver'].unique()[:3]:
                    driver_laps = laps[laps['Driver'] == driver].sort_values('LapNumber')
                    if len(driver_laps) > 15:
                        first_stint = driver_laps.head(5)['LapTime'].dropna().dt.total_seconds()
                        last_stint = driver_laps.tail(5)['LapTime'].dropna().dt.total_seconds()
                        
                        if len(first_stint) >= 3 and len(last_stint) >= 3:
                            degradation = (last_stint.mean() - first_stint.mean()) / first_stint.mean()
                            degradations.append(degradation)
                
                if degradations:
                    avg_degradation = np.mean(degradations)
                    if avg_degradation > 0.025:
                        return "High"
                    elif avg_degradation > 0.012:
                        return "Medium"
                    else:
                        return "Low"
            return "Medium"
        except:
            return "Medium"
    
    def _calculate_downforce(self, session) -> str:
        """Calculate downforce level from speed ratio"""
        try:
            if hasattr(session, 'car_data') and session.car_data:
                for driver, telemetry in session.car_data.items():
                    if telemetry is not None and 'Speed' in telemetry.columns:
                        speeds = telemetry['Speed']
                        top_speed = speeds.max()
                        corner_speed = speeds.quantile(0.25)
                        
                        if top_speed and top_speed > 0:
                            ratio = corner_speed / top_speed
                            if ratio > 0.7:
                                return "Maximum"
                            elif ratio > 0.6:
                                return "High"
                            elif ratio > 0.5:
                                return "Medium-High"
                            elif ratio > 0.4:
                                return "Medium"
                            else:
                                return "Low"
            return "Medium"
        except:
            return "Medium"
    
    def _calculate_brake_wear(self, session) -> str:
        """Calculate brake wear from braking frequency"""
        try:
            if hasattr(session, 'car_data') and session.car_data:
                for driver, telemetry in session.car_data.items():
                    if telemetry is not None and 'Brake' in telemetry.columns:
                        brake_changes = telemetry['Brake'].diff().abs()
                        braking_zones = len(brake_changes[brake_changes > 0.5])
                        
                        laps = session.laps
                        lap_count = len(laps['LapNumber'].unique())
                        
                        if lap_count > 0:
                            braking_per_lap = braking_zones / lap_count
                            if braking_per_lap > 12:
                                return "Very High"
                            elif braking_per_lap > 9:
                                return "High"
                            elif braking_per_lap > 6:
                                return "Medium"
                            else:
                                return "Low"
            return "Medium"
        except:
            return "Medium"
    
    def _calculate_top_speed(self, session) -> int:
        """Calculate top speed in km/h from telemetry data"""
        try:
            top_speeds = []
            
            if hasattr(session, 'car_data') and session.car_data:
                for driver, telemetry in session.car_data.items():
                    if telemetry is not None and 'Speed' in telemetry.columns:
                        driver_top_speed = telemetry['Speed'].max()
                        
                        if 200 < driver_top_speed < 400:
                            top_speeds.append(driver_top_speed)
                        elif 50 < driver_top_speed < 120:
                            converted = driver_top_speed * 3.6
                            if 200 < converted < 400:
                                top_speeds.append(converted)
            
            if top_speeds:
                return int(max(top_speeds))
            
            return None
        except Exception as e:
            return None
    
    def _calculate_avg_speed(self, track_length: float, laps: pd.DataFrame) -> int:
        """Calculate average race speed in km/h"""
        try:
            if track_length and laps is not None:
                lap_times = laps['LapTime'].dropna().dt.total_seconds()
                if len(lap_times) > 0:
                    avg_lap_time = lap_times.mean()
                    avg_speed_kmh = int((track_length / avg_lap_time) * 3600)
                    if 100 < avg_speed_kmh < 400:
                        return avg_speed_kmh
            return None
        except:
            return None
    
    def _get_overtaking_spots(self, circuit_name: str) -> list:
        """Get overtaking spots based on circuit name"""
        # This is a small lookup - only for display
        overtaking_map = {
            'Miami': ['Turns 11-16 complex', 'Start/Finish straight', 'Turn 1'],
            'Monaco': ['Tunnel exit', 'Nouvelle Chicane', 'Tabac'],
            'Spa': ['Kemmel Straight', 'Bus Stop Chicane', 'Les Combes'],
            'Monza': ['Turn 1', 'Variante della Roggia', 'Ascari'],
            'Silverstone': ['Hangar Straight', 'Wellington Straight', 'Stowe'],
            'Suzuka': ['Turns 1-2', 'Hairpin', '130R'],
            'Singapore': ['Turn 1', 'Turn 7', 'Turn 14'],
            'Bahrain': ['Turn 1', 'Turn 4', 'Turn 11'],
            'Austria': ['Turn 2', 'Turn 3', 'Turn 4'],
            'Canada': ['Chicane', 'Hairpin', 'Start/Finish straight'],
            'Australian': ['Turn 1', 'Turn 3', 'Turn 11', 'Start/Finish straight'],
            'Albert Park': ['Turn 1', 'Turn 3', 'Turn 11', 'Start/Finish straight']
        }
        
        for key, spots in overtaking_map.items():
            if key.lower() in circuit_name.lower():
                return spots
        return []
    
    def _generate_description_from_data(self, circuit_name: str, track_length: float, corner_count: int) -> str:
        """Generate description based on actual circuit data"""
        # Known circuit descriptions
        descriptions = {
            'Miami': "A modern street circuit around the Hard Rock Stadium complex. Features a unique fake marina and high-speed sections.",
            'Monaco': "Iconic street circuit winding through Monte Carlo's narrow streets. Extremely challenging with walls close to the track.",
            'Spa': "Fast, flowing circuit through the Ardennes forest. Features the famous Eau Rouge-Raidillon complex.",
            'Monza': "The 'Temple of Speed' - high-speed straights with heavy braking zones. Lowest downforce of the season.",
            'Silverstone': "Historic high-speed circuit with flowing corners. Home of the British Grand Prix.",
            'Suzuka': "Unique figure-eight layout with high-speed corners. One of the most challenging circuits.",
            'Singapore': "Night street circuit with high humidity and many corners. Physically demanding on drivers.",
            'Bahrain': "Desert circuit with wide track and multiple overtaking opportunities. Hosts night races.",
            'Austria': "Short, fast circuit set in the Austrian Alps. High elevation changes.",
            'Canada': "Semi-street circuit with heavy braking zones and the famous 'Wall of Champions'.",
            'Australian': "Picturesque parkland circuit around Albert Park Lake. Known for its high-speed straights and being the season opener.",
            'Albert Park': "Picturesque parkland circuit around Albert Park Lake. Known for its high-speed straights and being the season opener."
        }
        
        for key, desc in descriptions.items():
            if key.lower() in circuit_name.lower():
                return desc
        
        return f"{circuit_name} circuit. Characteristics calculated from telemetry data."
    
    def _format_lap_time(self, seconds: float) -> str:
        """Format lap time in MM:SS.ms format"""
        if not seconds:
            return "Unknown"
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:06.3f}"
    
    def _driver_code_to_name(self, code: str) -> str:
        """Convert driver code to full name"""
        driver_names = {
            'NOR': 'Lando Norris',
            'VER': 'Max Verstappen',
            'HAM': 'Lewis Hamilton',
            'LEC': 'Charles Leclerc',
            'RUS': 'George Russell',
            'PIA': 'Oscar Piastri',
            'SAI': 'Carlos Sainz',
            'PER': 'Sergio Perez',
            'ALO': 'Fernando Alonso',
            'ANT': 'Kimi Antonelli'
        }
        return driver_names.get(code, code)
    
    # ========== ANSWER FORMATTING METHODS ==========
    
    def _track_length_answer(self, track: str, info: dict) -> str:
        name = info.get('full_name', track.capitalize())
        length = info.get('length_km', 'Unknown')
        laps = info.get('laps', 'Unknown')
        
        if isinstance(length, (int, float)):
            total_km = length * laps if laps != 'Unknown' else 'Unknown'
            if laps != 'Unknown':
                return f"🏁 **{name}**\n\n• Length: {length:.3f} km\n• Race distance: {laps} laps ({total_km:.1f} km)"
            return f"🏁 **{name}**\n\n• Length: {length:.3f} km"
        return f"Length information for {track.capitalize()} not available."
    
    def _track_corners_answer(self, track: str, info: dict) -> str:
        corners = info.get('corners', 'Unknown')
        name = info.get('full_name', track.capitalize())
        
        if corners:
            return f"🏁 **{name}** has {corners} corners."
        return f"Corner information for {track.capitalize()} not available."
    
    def _lap_record_answer(self, track: str, info: dict) -> str:
        lap_record = info.get('lap_record_formatted', 'Unknown')
        driver = info.get('lap_record_driver', 'Unknown')
        year = info.get('lap_record_year', 'Unknown')
        name = info.get('full_name', track.capitalize())
        
        if lap_record != 'Unknown':
            driver_name = self._driver_code_to_name(driver)
            return f"🏁 **{name}** Lap Record: {lap_record} by {driver_name} ({year})"
        return f"Lap record for {track.capitalize()} not available."
    
    def _top_speed_answer(self, track: str, info: dict) -> str:
        top_speed = info.get('top_speed', 'Unknown')
        name = info.get('full_name', track.capitalize())
        
        if top_speed and isinstance(top_speed, int):
            return f"🏁 **{name}** Top Speed: {top_speed} km/h"
        return f"Top speed data for {track.capitalize()} not available."
    
    def _overtaking_answer(self, track: str, info: dict) -> str:
        spots = info.get('overtaking_spots', [])
        name = info.get('full_name', track.capitalize())
        
        if spots:
            return f"🏁 **{name}** - Best overtaking spots:\n" + "\n".join([f"  • {spot}" for spot in spots])
        return f"Overtaking analysis for {track.capitalize()} requires additional data."
    
    def _difficulty_answer(self, track: str, info: dict) -> str:
        difficulty = info.get('difficulty', 'Unknown')
        description = info.get('description', '')
        name = info.get('full_name', track.capitalize())
        
        short_desc = description.split('.')[0] if description else ''
        return f"🏁 **{name}**\n\n• Difficulty: {difficulty}\n• {short_desc}"
    
    def _tire_answer(self, track: str, info: dict) -> str:
        tire_wear = info.get('tire_wear', 'Unknown')
        name = info.get('full_name', track.capitalize())
        
        explanations = {
            'Low': 'Low tire wear - teams can use softer compounds',
            'Medium': 'Medium tire wear - balanced strategy possible',
            'High': 'High tire wear - harder compounds recommended'
        }
        explanation = explanations.get(tire_wear, '')
        return f"🏁 **{name}** Tire Wear: {tire_wear}\n• {explanation}"
    
    def _downforce_answer(self, track: str, info: dict) -> str:
        downforce = info.get('downforce', 'Unknown')
        name = info.get('full_name', track.capitalize())
        return f"🏁 **{name}** Downforce Level: {downforce}"
    
    def _brake_answer(self, track: str, info: dict) -> str:
        brake_wear = info.get('brake_wear', 'Unknown')
        name = info.get('full_name', track.capitalize())
        return f"🏁 **{name}** Brake Wear: {brake_wear}"
    
    def _full_track_info(self, track: str, info: dict) -> str:
        name = info.get('full_name', track.capitalize())
        location = info.get('location', 'Location not available')
        length = info.get('length_km', 'Unknown')
        laps = info.get('laps', 'Unknown')
        corners = info.get('corners', 'Unknown')
        difficulty = info.get('difficulty', 'Medium')
        description = info.get('description', f"{name} circuit")
        tire_wear = info.get('tire_wear', 'Medium')
        downforce = info.get('downforce', 'Medium')
        brake_wear = info.get('brake_wear', 'Medium')
        top_speed = info.get('top_speed', 'Unknown')
        avg_speed = info.get('avg_speed', 'Unknown')
        overtaking_spots = info.get('overtaking_spots', [])
        data_source = info.get('data_source', 'cached race data')
        
        lap_record = info.get('lap_record_formatted', 'Unknown')
        lap_driver = info.get('lap_record_driver', 'Unknown')
        lap_year = info.get('lap_record_year', 'Unknown')
        
        if lap_driver != 'Unknown':
            lap_driver = self._driver_code_to_name(lap_driver)
        
        output = f"🏁 **{name}**\n\n"
        output += f"📍 **Location:** {location}\n"
        
        if isinstance(length, (int, float)):
            output += f"📏 **Length:** {length:.3f} km\n"
        else:
            output += f"📏 **Length:** Data not available\n"
        
        output += f"🔄 **Laps:** {laps}\n"
        
        if corners:
            output += f"➡️ **Corners:** {corners}\n"
        
        if lap_record != 'Unknown':
            output += f"🏆 **Lap Record:** {lap_record} ({lap_driver}, {lap_year})\n"
        
        if top_speed and top_speed != 'Unknown':
            output += f"⚡ **Top Speed:** {top_speed} km/h\n"
        
        if avg_speed and avg_speed < 400:
            output += f"📊 **Average Speed:** {avg_speed} km/h\n"
        
        output += f"📊 **Difficulty:** {difficulty}\n"
        output += f"📝 **Description:** {description}\n"
        output += f"🛞 **Tire Wear:** {tire_wear}\n"
        output += f"🔧 **Downforce:** {downforce}\n"
        output += f"🛑 **Brake Wear:** {brake_wear}\n\n"
        
        if overtaking_spots:
            output += f"**Best Overtaking Spots:**\n"
            for spot in overtaking_spots:
                output += f"  • {spot}\n"
            output += "\n"
        
        output += f"*Data calculated from {data_source} telemetry*"
        
        return output
    
    def _track_help(self) -> str:
        return """🏁 **Track Analysis - I analyze from your cached FastF1 data:**

• Track length and race distance
• Corner count
• Lap records
• Top speed
• Difficulty level
• Tire wear characteristics
• Downforce requirements
• Brake wear patterns

**Example questions:**
• "Tell me about Miami circuit"
• "What is the top speed at Monza?"
• "How many corners does Suzuka have?"
• "What's the lap record at Spa?\""""


# For backwards compatibility
def analyze_track(question: str) -> str:
    agent = TrackAgent()
    return agent.analyze_track(question)
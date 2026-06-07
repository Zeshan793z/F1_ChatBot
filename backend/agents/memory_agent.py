"""
Memory Agent - Maintains conversation context across questions
"""

import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict


class MemoryAgent:
    def __init__(self, memory_file: str = "data/conversation_memory.json"):
        """Initialize the Memory Agent"""
        print("🧠 Initializing Memory Agent...")
        
        self.memory_file = Path(__file__).parent.parent.parent / memory_file
        self.session_memory = {
            'current_session': {
                'conversation_history': [],
                'last_driver': None,
                'last_driver_name': None,
                'last_gp': None,
                'last_year': None,
                'last_topic': None,
                'last_result': None,
                'last_team': None,
                'last_teammate_code': None,
                'last_teammate_name': None
            },
            'long_term': {
                'driver_preferences': {},
                'frequently_asked': {},
                'team_drivers': {}
            }
        }
        
        # Load existing memory if available
        self._load_memory()
        
        print("✅ Memory Agent ready!")
    
    def _load_memory(self):
        """Load saved memory from file"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    if 'current_session' in saved:
                        self.session_memory['current_session'] = saved['current_session']
                    if 'long_term' in saved:
                        long_term = saved['long_term']
                        self.session_memory['long_term']['driver_preferences'] = long_term.get('driver_preferences', {})
                        self.session_memory['long_term']['frequently_asked'] = long_term.get('frequently_asked', {})
                        self.session_memory['long_term']['team_drivers'] = long_term.get('team_drivers', {})
                print(f"📚 Loaded memory from {self.memory_file}")
            except Exception as e:
                print(f"⚠️ Could not load memory: {e}")
    
    def _save_memory(self):
        """Save memory to file"""
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            memory_to_save = {
                'current_session': self.session_memory['current_session'],
                'long_term': {
                    'driver_preferences': self.session_memory['long_term']['driver_preferences'],
                    'frequently_asked': self.session_memory['long_term']['frequently_asked'],
                    'team_drivers': self.session_memory['long_term']['team_drivers']
                }
            }
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Could not save memory: {e}")
    
    def _get_teammate(self, driver_code: str, year: int = None, gp: str = None) -> str:
        """
        Dynamically find a driver's teammate using FastF1 data
        No hardcoded mappings - always fetches from actual race data
        """
        try:
            import fastf1
            from pathlib import Path
            
            cache_dir = Path(__file__).parent.parent.parent / "data" / "fastf1_cache"
            fastf1.Cache.enable_cache(str(cache_dir))
            
            # Use the year and GP from memory
            if not year:
                year = self.session_memory['current_session'].get('last_year')
            if not gp:
                gp = self.session_memory['current_session'].get('last_gp')
            
            # If still missing, try to find any race with this driver
            if not year or not gp:
                print(f"🔍 No year/GP in memory, searching for driver {driver_code} in cache...")
                years = [2026, 2025, 2024, 2023]
                for y in years:
                    try:
                        schedule = fastf1.get_event_schedule(y)
                        races = schedule[schedule['Session5'] == 'Race']
                        for idx, race in races.iterrows():
                            gp_name = race['EventName']
                            try:
                                session = fastf1.get_session(y, gp_name, "R")
                                session.load(telemetry=False, laps=False, weather=False)
                                results = session.results
                                if driver_code in results['Abbreviation'].values:
                                    year = y
                                    gp = gp_name
                                    print(f"  Found {driver_code} in {year} {gp}")
                                    break
                            except:
                                continue
                        if year and gp:
                            break
                    except:
                        continue
            
            if not year:
                year = 2026
                print(f"  Using default year: {year}")
            
            if not gp:
                gp = "Japanese Grand Prix"
                print(f"  Using default GP: {gp}")
            
            print(f"🔍 Fetching teammate for {driver_code} at {year} {gp}")
            
            session = fastf1.get_session(year, gp, "R")
            session.load(telemetry=False, laps=False, weather=False)
            results = session.results
            
            # Find the driver's row
            driver_row = results[results['Abbreviation'] == driver_code]
            if driver_row.empty:
                print(f"⚠️ Driver {driver_code} not found in {year} {gp}")
                return None
            
            driver_team = driver_row.iloc[0]['TeamName']
            driver_name = driver_row.iloc[0]['FullName']
            print(f"🔍 {driver_name} ({driver_code}) is in team: {driver_team}")
            
            # Find ALL drivers in the same team
            team_drivers = []
            for idx, row in results.iterrows():
                if row['TeamName'] == driver_team:
                    team_drivers.append({
                        'code': row['Abbreviation'],
                        'name': row['FullName']
                    })
                    print(f"    Team member: {row['Abbreviation']} ({row['FullName']})")
            
            # Find the teammate (different driver, same team)
            for teammate in team_drivers:
                if teammate['code'] != driver_code:
                    teammate_code = teammate['code']
                    teammate_name = teammate['name']
                    print(f"🔍 Found teammate: {teammate_code} ({teammate_name})")
                    
                    # Store for later use
                    self.session_memory['current_session']['last_teammate_code'] = teammate_code
                    self.session_memory['current_session']['last_teammate_name'] = teammate_name
                    
                    return teammate_code
            
            print(f"⚠️ No teammate found for {driver_code} in {driver_team}")
            return None
            
        except Exception as e:
            print(f"⚠️ Could not fetch teammate dynamically: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def extract_context(self, question: str, answer: str) -> dict:
        """Extract key information from Q&A pair for memory"""
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        context = {}
        
        print(f"🧠 Extracting context from Q: {question[:50]}...")
        print(f"🧠 Extracting context from A: {answer[:50]}...")
        
        # Driver mapping with variations
        driver_map = {
            'verstappen': ('VER', 'Verstappen'), 'max': ('VER', 'Verstappen'),
            'hamilton': ('HAM', 'Hamilton'), 'lewis': ('HAM', 'Hamilton'),
            'leclerc': ('LEC', 'Leclerc'), 'charles': ('LEC', 'Leclerc'),
            'norris': ('NOR', 'Norris'), 'lando': ('NOR', 'Norris'),
            'russell': ('RUS', 'Russell'), 'george': ('RUS', 'Russell'),
            'piastri': ('PIA', 'Piastri'), 'oscar': ('PIA', 'Piastri'),
            'sainz': ('SAI', 'Sainz'), 'carlos': ('SAI', 'Sainz'),
            'perez': ('PER', 'Perez'), 'checo': ('PER', 'Perez'),
            'alonso': ('ALO', 'Alonso'), 'fernando': ('ALO', 'Alonso'),
            'antonelli': ('ANT', 'Antonelli'), 'kimi': ('ANT', 'Antonelli')
        }
        
        # Method 1: Look for driver name in answer (e.g., "Kimi Antonelli")
        for name, (code, full_name) in driver_map.items():
            if name in answer_lower:
                context['driver'] = code
                context['driver_name'] = full_name
                print(f"🧠 Stored driver from answer: {full_name} ({code})")
                break
        
        # Method 2: Look for driver code in parentheses like (ANT)
        if 'driver' not in context:
            code_match = re.search(r'\(([A-Z]{3})\)', answer)
            if code_match:
                code = code_match.group(1)
                # Map code to name
                code_to_name = {
                    'VER': 'Verstappen', 'HAM': 'Hamilton', 'LEC': 'Leclerc',
                    'NOR': 'Norris', 'RUS': 'Russell', 'PIA': 'Piastri',
                    'SAI': 'Sainz', 'PER': 'Perez', 'ALO': 'Alonso', 'ANT': 'Antonelli'
                }
                if code in code_to_name:
                    context['driver'] = code
                    context['driver_name'] = code_to_name[code]
                    print(f"🧠 Stored driver from code in parentheses: {code_to_name[code]} ({code})")
        
        # Method 3: Look for driver name in question
        if 'driver' not in context:
            for name, (code, full_name) in driver_map.items():
                if name in question_lower:
                    context['driver'] = code
                    context['driver_name'] = full_name
                    print(f"🧠 Stored driver from question: {full_name} ({code})")
                    break
        
        # Extract year from question or answer
        year_match = re.search(r'\b20(2[3-6])\b', question_lower)
        if not year_match:
            year_match = re.search(r'\b20(2[3-6])\b', answer_lower)
        if year_match:
            context['year'] = int(year_match.group(0))
            print(f"🧠 Extracted year: {context['year']}")
        
        # Extract GP from question or answer
        gp_list = ['miami', 'monaco', 'canadian', 'british', 'austrian', 
                   'belgian', 'italian', 'singapore', 'abu dhabi', 'dutch',
                   'spanish', 'hungarian', 'mexico', 'brazil', 'australian',
                   'chinese', 'japanese']
        
        for gp_name in gp_list:
            if gp_name in question_lower:
                context['gp'] = gp_name.capitalize() + " Grand Prix"
                print(f"🧠 Extracted GP from question: {context['gp']}")
                break
            elif gp_name in answer_lower and 'gp' not in context:
                context['gp'] = gp_name.capitalize() + " Grand Prix"
                print(f"🧠 Extracted GP from answer: {context['gp']}")
                break
        
        # Track topic
        if 'weather' in question_lower:
            context['topic'] = 'weather'
        elif 'strategy' in question_lower or 'pit' in question_lower or 'tire' in question_lower:
            context['topic'] = 'strategy'
        elif 'compare' in question_lower or 'vs' in question_lower:
            context['topic'] = 'comparison'
        else:
            context['topic'] = 'factual'
        
        print(f"🧠 Final context: {context}")
        return context
    
    def update_memory(self, question: str, answer: str):
        """Update memory with new Q&A pair"""
        context = self.extract_context(question, answer)
        
        print(f"🧠 Updating memory with context: {context}")
        
        # Add to conversation history
        self.session_memory['current_session']['conversation_history'].append({
            'question': question,
            'answer': answer[:500],
            'timestamp': datetime.now().isoformat(),
            'context': context
        })
        
        # Keep only last 20 conversations
        if len(self.session_memory['current_session']['conversation_history']) > 20:
            self.session_memory['current_session']['conversation_history'] = \
                self.session_memory['current_session']['conversation_history'][-20:]
        
        # Update last context - ALWAYS update if driver is in context
        if 'driver' in context:
            self.session_memory['current_session']['last_driver'] = context['driver']
            self.session_memory['current_session']['last_driver_name'] = context.get('driver_name')
            print(f"🧠 Stored in memory: driver={context['driver']}, name={context.get('driver_name')}")
        else:
            # If no driver found, don't clear existing memory
            print(f"🧠 No driver found in context, keeping existing memory")
        
        if 'gp' in context:
            self.session_memory['current_session']['last_gp'] = context['gp']
            print(f"🧠 Stored GP: {context['gp']}")
        if 'year' in context:
            self.session_memory['current_session']['last_year'] = context['year']
            print(f"🧠 Stored year: {context['year']}")
        if 'topic' in context:
            self.session_memory['current_session']['last_topic'] = context['topic']
        
        self.session_memory['current_session']['last_result'] = answer[:200]
        
        print(f"🧠 Memory after update: last_driver={self.session_memory['current_session']['last_driver']}, last_driver_name={self.session_memory['current_session']['last_driver_name']}")
        
        self._save_memory()
    
    def get_teammate_answer(self, question: str) -> str:
        """Directly answer teammate question without going through Data Agent"""
        last_driver = self.session_memory['current_session'].get('last_driver')
        last_driver_name = self.session_memory['current_session'].get('last_driver_name')
        last_year = self.session_memory['current_session'].get('last_year')
        last_gp = self.session_memory['current_session'].get('last_gp')
        
        print(f"🧠 Getting teammate for: last_driver={last_driver}, name={last_driver_name}, year={last_year}, gp={last_gp}")
        
        if not last_driver:
            return "I don't know which driver you're asking about. Please mention a specific driver first, like 'Who won the Japanese GP 2026?'"
        
        # Try to get driver name if not stored
        if not last_driver_name:
            driver_names = {
                'VER': 'Verstappen', 'HAM': 'Hamilton', 'LEC': 'Leclerc',
                'NOR': 'Norris', 'RUS': 'Russell', 'PIA': 'Piastri',
                'SAI': 'Sainz', 'PER': 'Perez', 'ALO': 'Alonso', 'ANT': 'Antonelli'
            }
            last_driver_name = driver_names.get(last_driver, last_driver)
        
        teammate_code = self._get_teammate(last_driver, last_year, last_gp)
        
        if teammate_code:
            driver_names = {
                'VER': 'Verstappen', 'HAM': 'Hamilton', 'LEC': 'Leclerc',
                'NOR': 'Norris', 'RUS': 'Russell', 'PIA': 'Piastri',
                'SAI': 'Sainz', 'PER': 'Perez', 'ALO': 'Alonso', 'ANT': 'Antonelli'
            }
            teammate_name = driver_names.get(teammate_code, teammate_code)
            
            gp_context = f" at the {last_gp}" if last_gp else ""
            year_context = f" {last_year}" if last_year else ""
            
            return f"{last_driver_name}'s teammate{gp_context}{year_context} is {teammate_name}."
        
        return f"I couldn't find teammate information for {last_driver_name} in the {last_gp or 'race'} {last_year or ''}."
    
    def enhance_question(self, question: str) -> str:
        """
        Enhance a follow-up question with memory context
        """
        question_lower = question.lower()
        
        # ========== TEAMMATE QUESTION DETECTION - MOST IMPORTANT ==========
        # Check if this is asking about a teammate
        teammate_indicators = ['teammate', 'team mate', 'team-mate', 'his teammate', 'her teammate', 'their teammate']
        is_teammate_question = any(indicator in question_lower for indicator in teammate_indicators)
        
        if is_teammate_question:
            # Check if we have a last driver in memory
            if self.session_memory['current_session'].get('last_driver'):
                print(f"🧠 Teammate question detected for driver: {self.session_memory['current_session']['last_driver']}")
                return "___TEAMMATE_QUESTION___"
            else:
                print("🧠 Teammate question but no driver in memory")
                return "I don't know which driver you're asking about. Please mention a specific driver first."
        
        # Handle other pronoun resolutions for non-teammate questions
        has_explicit_driver = any(driver in question_lower for driver in 
                                  ['verstappen', 'hamilton', 'leclerc', 'norris', 'russell', 
                                   'piastri', 'sainz', 'perez', 'alonso', 'antonelli'])
        
        enhanced = question
        
        if not has_explicit_driver and self.session_memory['current_session'].get('last_driver'):
            driver_names = {
                'VER': 'Verstappen', 'HAM': 'Hamilton', 'LEC': 'Leclerc',
                'NOR': 'Norris', 'RUS': 'Russell', 'PIA': 'Piastri',
                'SAI': 'Sainz', 'PER': 'Perez', 'ALO': 'Alonso', 'ANT': 'Antonelli'
            }
            driver_name = driver_names.get(self.session_memory['current_session']['last_driver'], 'the driver')
            
            if 'his' in question_lower or 'her' in question_lower or 'their' in question_lower:
                enhanced = enhanced.replace('his', f"{driver_name}'s")
                enhanced = enhanced.replace('her', f"{driver_name}'s")
                enhanced = enhanced.replace('their', f"{driver_name}'s")
            elif 'he' in question_lower or 'she' in question_lower or 'they' in question_lower:
                enhanced = enhanced.replace('he', driver_name)
                enhanced = enhanced.replace('she', driver_name)
                enhanced = enhanced.replace('they', driver_name)
            elif 'him' in question_lower or 'her' in question_lower or 'them' in question_lower:
                enhanced = enhanced.replace('him', driver_name)
                enhanced = enhanced.replace('her', driver_name)
                enhanced = enhanced.replace('them', driver_name)
        
        # Handle year context
        if not re.search(r'20(2[3-6])', question_lower) and self.session_memory['current_session'].get('last_year'):
            year = self.session_memory['current_session']['last_year']
            if 'previous' in question_lower or 'before' in question_lower:
                enhanced = enhanced.replace('previous', f"{year - 1}")
                enhanced = enhanced.replace('before', f"before {year}")
            elif 'next' in question_lower or 'after' in question_lower:
                enhanced = enhanced.replace('next', f"{year + 1}")
                enhanced = enhanced.replace('after', f"after {year}")
            else:
                if str(year) not in enhanced:
                    enhanced = f"{enhanced} {year}"
        
        # Handle GP context
        gp_list = ['miami', 'monaco', 'canadian', 'british', 'austrian', 
                   'belgian', 'italian', 'singapore', 'abu dhabi', 'dutch',
                   'japanese', 'australian', 'chinese']
        
        has_gp = any(gp in question_lower for gp in gp_list)
        last_gp = self.session_memory['current_session'].get('last_gp')
        
        if not has_gp and last_gp:
            gp_short = last_gp.replace(' Grand Prix', '')
            if 'that race' in question_lower or 'that gp' in question_lower:
                enhanced = enhanced.replace('that race', f"the {gp_short} Grand Prix")
                enhanced = enhanced.replace('that gp', f"the {gp_short} Grand Prix")
            else:
                if ' at ' not in question_lower and ' in ' not in question_lower:
                    if gp_short.lower() not in enhanced.lower():
                        enhanced = f"{enhanced} at the {gp_short} Grand Prix"
        
        print(f"🧠 Enhanced question: {enhanced}")
        return enhanced
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation context"""
        memory = self.session_memory['current_session']
        
        if not memory['conversation_history']:
            return "No previous conversation."
        
        summary = f"Previously discussed: {len(memory['conversation_history'])} exchanges. "
        
        if memory.get('last_driver_name'):
            summary += f"Last talking about {memory['last_driver_name']}. "
        
        if memory.get('last_gp'):
            summary += f"Context: {memory['last_gp']}. "
        
        if memory.get('last_topic'):
            summary += f"Topic: {memory['last_topic']}. "
        
        return summary
    
    def clear_session(self):
        """Clear current session memory (start fresh)"""
        self.session_memory['current_session'] = {
            'conversation_history': [],
            'last_driver': None,
            'last_driver_name': None,
            'last_gp': None,
            'last_year': None,
            'last_topic': None,
            'last_result': None,
            'last_team': None,
            'last_teammate_code': None,
            'last_teammate_name': None
        }
        self._save_memory()
        print("🧠 Session memory cleared!")
    
    def get_stats(self) -> dict:
        """Get memory statistics"""
        return {
            'conversation_length': len(self.session_memory['current_session']['conversation_history']),
            'favorite_drivers': self.session_memory['long_term']['driver_preferences'],
            'favorite_topics': self.session_memory['long_term']['frequently_asked'],
            'last_driver': self.session_memory['current_session'].get('last_driver_name'),
            'last_gp': self.session_memory['current_session'].get('last_gp'),
            'last_year': self.session_memory['current_session'].get('last_year')
        }
from langchain_community.llms import GPT4All
from pathlib import Path
import warnings
import re
import json
from typing import List, Tuple, Optional
from collections import Counter

warnings.filterwarnings("ignore", message="Failed to load llamamodel*")

class F1RAGAgent:
    def __init__(self):
        self.model_path = Path(__file__).parent.parent / "models" / "Meta-Llama-3-8B-Instruct.Q4_0.gguf"
        print(f"Looking for model at: {self.model_path}")
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        
        self.llm = GPT4All(model=str(self.model_path), verbose=False)
        self.is_initialized = False
        self.knowledge_base = []
        self.winners_cache = {}  # Cache for winners by year
        
        # Path to cache file
        self.cache_file = Path(__file__).parent.parent.parent / "data" / "f1_knowledge_cache.json"
        
    def initialize_knowledge_base(self, force_reload: bool = False):
        """Initialize F1 knowledge base - loads from cache if available"""
        
        # Try to load from cache file first
        if not force_reload and self.cache_file.exists():
            print(f"📚 Loading F1 knowledge base from cache: {self.cache_file}")
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.knowledge_base = cache_data.get('knowledge_base', [])
                    # Convert winners cache back from JSON (keys are strings)
                    self.winners_cache = {}
                    for year, winners in cache_data.get('winners_cache', {}).items():
                        self.winners_cache[int(year)] = winners
                    self.is_initialized = True
                    print(f"✅ Loaded {len(self.knowledge_base)} documents from cache")
                    return
            except Exception as e:
                print(f"⚠️ Could not load cache: {e}")
        
        # If cache doesn't exist or force_reload, build from FastF1
        print("📚 Building F1 Knowledge Base from FastF1 cache...")
        self._build_from_fastf1()
        
        # Save to cache for next time
        self._save_to_cache()
    
    def _build_from_fastf1(self):
        """Build knowledge base from FastF1 - extracts ALL data (tires, weather, telemetry, pit stops)"""
        try:
            import fastf1
            import pandas as pd
            from datetime import datetime
            
            cache_dir = Path(__file__).parent.parent.parent / "data" / "fastf1_cache"
            fastf1.Cache.enable_cache(str(cache_dir))
            
            years = [2026, 2025, 2024, 2023]
            knowledge_texts = []
            current_date = datetime.now()
            
            for year in years:
                print(f"\n📅 Processing {year} season...")
                try:
                    schedule = fastf1.get_event_schedule(year)
                    races = schedule[schedule['Session5'] == 'Race'] if 'Session5' in schedule.columns else schedule
                    print(f"  Found {len(races)} races")
                    
                    year_winners = []
                    
                    for idx, race in races.iterrows():
                        gp_name = race['EventName']
                        
                        # Skip future races
                        race_date = race['EventDate']
                        if isinstance(race_date, pd.Timestamp):
                            race_date = race_date.to_pydatetime()
                        
                        if race_date > current_date:
                            print(f"    ⏭️ Skipping future race: {gp_name}")
                            continue
                        
                        try:
                            # Load with telemetry=True and weather=True
                            session = fastf1.get_session(year, gp_name, "R")
                            session.load(telemetry=True, laps=True, weather=True)
                            
                            results = session.results
                            if not results.empty:
                                winner = results.iloc[0]
                                winner_code = winner['Abbreviation']
                                winner_name = winner['FullName']
                                winner_team = winner['TeamName']
                                
                                year_winners.append(winner_code)
                                
                                # Store in winners_cache (preserves existing structure)
                                if year not in self.winners_cache:
                                    self.winners_cache[year] = []
                                self.winners_cache[year].append({
                                    'gp': gp_name,
                                    'driver_code': winner_code,
                                    'driver_name': winner_name,
                                    'team': winner_team
                                })
                                
                                # Build text - PRESERVES existing format
                                text = f"[{year}] {gp_name} WINNER: {winner_code} ({winner_name}) - {winner_team}"
                                
                                # Get fastest lap with TIRE COMPOUND
                                fastest = session.laps.pick_fastest()
                                if fastest is not None and not fastest.empty:
                                    fastest_time = fastest['LapTime'].total_seconds()
                                    fastest_driver = fastest['Driver']
                                    text += f" | FASTEST LAP: {fastest_driver} - {fastest_time:.3f}s"
                                    
                                    # ADD TIRE COMPOUND (new)
                                    if 'Compound' in fastest.index:
                                        tire = fastest['Compound']
                                        if pd.notna(tire):
                                            text += f" | TIRE: {tire}"
                                
                                # ADD WEATHER DATA (new)
                                if hasattr(session, 'weather_data') and session.weather_data is not None:
                                    weather = session.weather_data
                                    if not weather.empty:
                                        weather_parts = []
                                        if 'AirTemp' in weather.columns:
                                            air_temp = weather['AirTemp'].mean()
                                            if pd.notna(air_temp):
                                                weather_parts.append(f"Air:{air_temp:.0f}°C")
                                        if 'TrackTemp' in weather.columns:
                                            track_temp = weather['TrackTemp'].mean()
                                            if pd.notna(track_temp):
                                                weather_parts.append(f"Track:{track_temp:.0f}°C")
                                        if 'Humidity' in weather.columns:
                                            humidity = weather['Humidity'].mean()
                                            if pd.notna(humidity):
                                                weather_parts.append(f"Humidity:{humidity:.0f}%")
                                        if weather_parts:
                                            text += f" | WEATHER: {' | '.join(weather_parts)}"
                                
                                # ADD PIT STOP SUMMARY (new)
                                if hasattr(session, 'laps') and session.laps is not None:
                                    pit_stops = session.laps.dropna(subset=['PitInTime'])
                                    if not pit_stops.empty:
                                        pit_counts = pit_stops['Driver'].value_counts()
                                        pit_summary = [f"{d}:{c}" for d, c in pit_counts.head(3).items()]
                                        if pit_summary:
                                            text += f" | PIT STOPS: {', '.join(pit_summary)}"
                                
                                # ADD SECTOR TIMES for fastest lap (new)
                                if fastest is not None and not fastest.empty:
                                    sector_parts = []
                                    if 'Sector1Time' in fastest.index and pd.notna(fastest['Sector1Time']):
                                        sector_parts.append(f"S1:{fastest['Sector1Time'].total_seconds():.3f}")
                                    if 'Sector2Time' in fastest.index and pd.notna(fastest['Sector2Time']):
                                        sector_parts.append(f"S2:{fastest['Sector2Time'].total_seconds():.3f}")
                                    if 'Sector3Time' in fastest.index and pd.notna(fastest['Sector3Time']):
                                        sector_parts.append(f"S3:{fastest['Sector3Time'].total_seconds():.3f}")
                                    if sector_parts:
                                        text += f" | SECTORS: {' | '.join(sector_parts)}"
                                
                                knowledge_texts.append(text)
                                print(f"    ✅ {gp_name}: {winner_name} ({winner_code}) - TIRE: {tire if 'tire' in locals() else 'N/A'}")
                                
                        except Exception as e:
                            if "no data" not in str(e).lower() and "404" not in str(e):
                                print(f"    ⚠️ Could not load {gp_name}: {str(e)[:80]}")
                            continue
                    
                    # Calculate championship leader (preserves existing functionality)
                    if year_winners:
                        win_counts = Counter(year_winners)
                        leader = win_counts.most_common(1)[0]
                        leader_code = leader[0]
                        leader_wins = leader[1]
                        
                        leader_name = leader_code
                        for winner in self.winners_cache.get(year, []):
                            if winner['driver_code'] == leader_code:
                                leader_name = winner['driver_name']
                                break
                        
                        knowledge_texts.append(f"[{year}] SEASON LEADER: {leader_name} ({leader_code}) with {leader_wins} wins")
                        print(f"  🏆 {year} Season Leader: {leader_name} ({leader_code}) - {leader_wins} wins")
                        
                except Exception as e:
                    print(f"  ❌ Error loading {year}: {e}")
                    continue
            
            self.knowledge_base = knowledge_texts
            self.is_initialized = True
            self._save_to_cache()
            print(f"\n✅ Total: {len(self.knowledge_base)} F1 documents loaded")
            
        except Exception as e:
            print(f"⚠️ Could not load FastF1 data: {e}")
            self._load_fallback_knowledge()
            self.is_initialized = True
    
    def _save_to_cache(self):
        """Save knowledge base to cache file"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_data = {
                'knowledge_base': self.knowledge_base,
                'winners_cache': {str(year): winners for year, winners in self.winners_cache.items()}
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved {len(self.knowledge_base)} documents to cache: {self.cache_file}")
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")
    
    def _load_fallback_knowledge(self):
        """Fallback knowledge base with essential F1 facts"""
        self.knowledge_base = [
            "[2026] Current F1 World Champion: TBD",
            "[2025] F1 World Champion: Max Verstappen (Red Bull Racing)",
            "[2024] F1 World Champion: Max Verstappen (Red Bull Racing)",
            "[2023] F1 World Champion: Max Verstappen (Red Bull Racing)",
            "F1 champions: 2021-2025 Max Verstappen, 2020 Lewis Hamilton, 2019 Lewis Hamilton",
            "Most constructors titles: Ferrari (16), Williams (9), McLaren (8), Mercedes (8)",
            "Most wins: Lewis Hamilton (105), Michael Schumacher (91), Sebastian Vettel (53)",
            "DRS: Drag Reduction System, opens rear wing to aid overtaking",
            "Pirelli tire compounds: C1 (hardest) to C5 (softest)"
        ]
        print(f"✅ Loaded {len(self.knowledge_base)} fallback F1 documents")
    
    def reload_knowledge_base(self):
        """Force reload from FastF1 (useful when new race data is available)"""
        print("🔄 Force reloading knowledge base from FastF1...")
        self._build_from_fastf1()
        self._save_to_cache()
    
    def get_latest_champion(self, specific_year: int = None) -> Optional[str]:
        """Get the championship leader for a specific year or latest year"""
        
        # If year specified, get that year's champion
        if specific_year and specific_year in self.winners_cache:
            # Count wins for that year
            winners = [w['driver_code'] for w in self.winners_cache[specific_year]]
            if winners:
                win_counts = Counter(winners)
                leader = win_counts.most_common(1)[0]
                leader_code = leader[0]
                
                # Find full name
                for w in self.winners_cache[specific_year]:
                    if w['driver_code'] == leader_code:
                        return w['driver_name']
                return leader_code
        
        # Otherwise, get latest year's champion
        for year in [2026, 2025, 2024, 2023]:
            if year in self.winners_cache and self.winners_cache[year]:
                winners = [w['driver_code'] for w in self.winners_cache[year]]
                if winners:
                    win_counts = Counter(winners)
                    leader = win_counts.most_common(1)[0]
                    leader_code = leader[0]
                    
                    for w in self.winners_cache[year]:
                        if w['driver_code'] == leader_code:
                            return w['driver_name']
                    return leader_code
        
        return None
    
    def get_race_winner(self, year: int, gp_name: str) -> Optional[str]:
        """Get winner for a specific race"""
        if year in self.winners_cache:
            for race in self.winners_cache[year]:
                if gp_name.lower() in race['gp'].lower():
                    return race['driver_name']
        return None
    
    def search_knowledge(self, question: str, k: int = 3) -> List[Tuple[str, float]]:
        """Smart search that finds the most relevant documents"""
        question_lower = question.lower()
        scored_docs = []
        
        # Extract key terms from question (ignore common words)
        stop_words = ['what', 'when', 'where', 'which', 'how', 'the', 'and', 'for', 'with', 'was', 'were', 'did']
        key_terms = []
        for word in question_lower.split():
            if len(word) > 2 and word not in stop_words:
                key_terms.append(word)
        
        # Year weights for recency
        year_weights = {2026: 150, 2025: 100, 2024: 50, 2023: 25}
        
        for doc in self.knowledge_base:
            doc_lower = doc.lower()
            score = 0
            
            # Score based on key terms
            for term in key_terms:
                if term in doc_lower:
                    score += 3
            
            # Score based on year match
            year_match = re.search(r'202[3-6]', question)
            if year_match:
                if f'[{year_match.group(0)}]' in doc:
                    score += 10
            
            # Score based on GP match
            gp_terms = ['australian', 'chinese', 'japanese', 'miami', 'canadian', 
                        'monaco', 'british', 'austrian', 'belgian', 'italian',
                        'singapore', 'abu dhabi', 'bahrain', 'saudi', 'azerbaijan',
                        'spanish', 'hungarian', 'dutch', 'mexico', 'brazil', 'qatar']
            for gp in gp_terms:
                if gp in question_lower and gp in doc_lower:
                    score += 8
            
            # Extract year for recency bonus
            year = None
            if doc.startswith('[2026]'):
                year = 2026
            elif doc.startswith('[2025]'):
                year = 2025
            elif doc.startswith('[2024]'):
                year = 2024
            elif doc.startswith('[2023]'):
                year = 2023
            
            recency_bonus = year_weights.get(year, 0) if year else 0
            total_score = score + recency_bonus
            
            if total_score > 0:
                scored_docs.append((doc, total_score))
        
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs[:k]
    
    def is_f1_question(self, question: str) -> bool:
        """Check if question is F1-related - more comprehensive matching"""
        question_lower = question.lower()
        
        # Core F1 terms
        f1_keywords = [
            'formula', 'f1', 'grand prix', 'gp', 'ferrari', 'mercedes', 'red bull',
            'verstappen', 'hamilton', 'leclerc', 'norris', 'perez', 'sainz',
            'antonelli', 'russell', 'piastri', 'alonso', 'vettel', 'schumacher',
            'pirelli', 'drs', 'ers', 'drag reduction', 'pit stop', 'qualifying',
            'sprint', 'race', 'championship', 'constructor', 'driver', 'circuit',
            'monza', 'monaco', 'silverstone', 'spa', 'suzuka', 'miami', 'vegas',
            'canada', 'canadian', 'australia', 'australian', 'china', 'chinese',
            'japan', 'japanese', 'britain', 'british', 'austria', 'austrian',
            'belgium', 'belgian', 'italy', 'italian', 'singapore', 'abu dhabi',
            'bahrain', 'saudi', 'azerbaijan', 'spain', 'spanish', 'hungary',
            'hungarian', 'netherlands', 'dutch', 'mexico', 'mexican', 'brazil',
            'brazilian', 'qatar', 'las vegas', 'cota', 'austin', 'imola',
            'portimao', 'zandvoort', 'baku', 'istanbul', 'melbourne'
        ]
        
        question_lower = question.lower()
        
        # Check for F1 keywords
        if any(keyword in question_lower for keyword in f1_keywords):
            return True
        
        # Check for year mentions with racing context
        if re.search(r'202[3-6]', question) and any(word in question_lower for word in ['race', 'won', 'winner', 'champion', 'gp']):
            return True
        
        # Check for driver names (common F1 drivers)
        driver_names = [
            'max', 'verstappen', 'lewis', 'hamilton', 'charles', 'leclerc',
            'lando', 'norris', 'carlos', 'sainz', 'sergio', 'perez',
            'george', 'russell', 'oscar', 'piastri', 'kimi', 'antonelli',
            'fernando', 'alonso', 'sebastian', 'vettel', 'daniel', 'ricciardo'
        ]
        if any(name in question_lower for name in driver_names):
            return True
        
        return False
    def chat(self, question: str) -> str:
        """Answer ANY F1 question naturally - with full details from the data"""
        if not self.is_f1_question(question):
            return "I'm specialized in Formula 1. Please ask me about F1 racing! 🏎️"
        
        # Search for relevant documents
        relevant_docs = self.search_knowledge(question, k=3)
        
        if not relevant_docs:
            return "I don't have information about that in my F1 database."
        
        context = "\n\n".join([doc for doc, _ in relevant_docs])
        
        # More flexible prompt for "tell me about" questions
        prompt = f"""Based ONLY on the F1 data below, answer the question naturally and conversationally.

    DATA: {context}

    QUESTION: {question}

    INSTRUCTIONS:
    - Answer in 2-3 sentences
    - Include key facts: winner, fastest lap, tire compound, weather
    - Be conversational but factual

    ANSWER:"""
        
        try:
            response = self.llm.invoke(prompt)
            
            # Clean up
            response = response.strip()
            response = re.sub(r'^ANSWER:\s*', '', response, flags=re.IGNORECASE)
            response = re.sub(r'<[^>]+>', '', response)
            response = re.sub(r'\s+', ' ', response)
            
            return response if response else "I don't have that information."
            
        except Exception as e:
            return f"Error: {str(e)}"
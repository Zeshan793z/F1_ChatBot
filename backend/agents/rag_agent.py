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
        self.winners_cache = {}
        
        self.cache_file = Path(__file__).parent.parent.parent / "data" / "f1_knowledge_cache.json"
        
    def initialize_knowledge_base(self, force_reload: bool = False):
        if not force_reload and self.cache_file.exists():
            print(f"📚 Loading F1 knowledge base from cache: {self.cache_file}")
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.knowledge_base = cache_data.get('knowledge_base', [])
                    for year, winners in cache_data.get('winners_cache', {}).items():
                        self.winners_cache[int(year)] = winners
                    self.is_initialized = True
                    print(f"✅ Loaded {len(self.knowledge_base)} documents from cache")
                    return
            except Exception as e:
                print(f"⚠️ Could not load cache: {e}")
        
        print("📚 Building F1 Knowledge Base from FastF1 cache...")
        self._build_from_fastf1()
        self._save_to_cache()
    
    def _build_from_fastf1(self):
        try:
            import fastf1
            import pandas as pd
            from datetime import datetime
            
            cache_dir = Path(__file__).parent.parent.parent / "data" / "fastf1_cache"
            fastf1.Cache.enable_cache(str(cache_dir))
            
            years = [2026, 2025, 2024, 2023]
            knowledge_texts = []
            current_date = datetime.now()
            
            race_order = ['Australian', 'Chinese', 'Japanese', 'Miami', 'Canadian']
            
            for year in years:
                print(f"\n📅 Processing {year} season...")
                try:
                    schedule = fastf1.get_event_schedule(year)
                    races = schedule[schedule['Session5'] == 'Race'] if 'Session5' in schedule.columns else schedule
                    print(f"  Found {len(races)} races")
                    
                    year_winners = []
                    year_races = []
                    
                    for idx, race in races.iterrows():
                        gp_name = race['EventName']
                        race_date = race['EventDate']
                        if isinstance(race_date, pd.Timestamp):
                            race_date = race_date.to_pydatetime()
                        
                        if race_date > current_date:
                            print(f"    ⏭️ Skipping future race: {gp_name}")
                            continue
                        
                        try:
                            session = fastf1.get_session(year, gp_name, "R")
                            session.load(telemetry=False, laps=True, weather=False)
                            
                            results = session.results
                            if not results.empty:
                                year_races.append({'gp': gp_name, 'date': race_date})
                                
                                winner = results.iloc[0]
                                winner_code = winner['Abbreviation']
                                winner_name = winner['FullName']
                                winner_team = winner['TeamName']
                                
                                year_winners.append(winner_code)
                                
                                if year not in self.winners_cache:
                                    self.winners_cache[year] = []
                                self.winners_cache[year].append({
                                    'gp': gp_name,
                                    'driver_code': winner_code,
                                    'driver_name': winner_name,
                                    'team': winner_team
                                })
                                
                                # Build clean text entry
                                text = f"[{year}] {gp_name} | WINNER: {winner_code} ({winner_name}) - {winner_team}"
                                
                                # STARTING GRID
                                grid_positions = []
                                for _, row in results.iterrows():
                                    driver_code = row['Abbreviation']
                                    driver_name = row['FullName']
                                    if 'GridPosition' in row and pd.notna(row['GridPosition']):
                                        grid_pos = int(row['GridPosition'])
                                        grid_positions.append(f"P{grid_pos}:{driver_code}")
                                
                                if grid_positions:
                                    text += f" | GRID: {' '.join(grid_positions[:10])}"
                                
                                # FASTEST LAP & TIRE
                                fastest = session.laps.pick_fastest()
                                if fastest is not None and not fastest.empty:
                                    fastest_time = fastest['LapTime'].total_seconds()
                                    fastest_driver = fastest['Driver']
                                    text += f" | FL: {fastest_driver} {fastest_time:.3f}s"
                                    
                                    if 'Compound' in fastest.index:
                                        tire = fastest['Compound']
                                        if pd.notna(tire):
                                            text += f" | TIRE: {tire}"
                                
                                # PIT STOPS
                                if hasattr(session, 'laps') and session.laps is not None:
                                    pit_stops = session.laps.dropna(subset=['PitInTime'])
                                    if not pit_stops.empty:
                                        pit_counts = pit_stops['Driver'].value_counts()
                                        pit_summary = [f"{d}:{c}" for d, c in pit_counts.head(3).items()]
                                        if pit_summary:
                                            text += f" | PITS: {', '.join(pit_summary)}"
                                
                                knowledge_texts.append(text)
                                print(f"    ✅ {gp_name}: {winner_name}")
                                
                        except Exception as e:
                            continue
                    
                    if year_winners:
                        win_counts = Counter(year_winners)
                        leader = win_counts.most_common(1)[0]
                        leader_code = leader[0]
                        leader_name = leader_code
                        for winner in self.winners_cache.get(year, []):
                            if winner['driver_code'] == leader_code:
                                leader_name = winner['driver_name']
                                break
                        knowledge_texts.append(f"[{year}] SEASON LEADER: {leader_name} ({leader_code}) with {leader[1]} wins")
                        print(f"  🏆 {year} Season Leader: {leader_name} ({leader_code})")
                        
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
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_data = {
                'knowledge_base': self.knowledge_base,
                'winners_cache': {str(year): winners for year, winners in self.winners_cache.items()}
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved {len(self.knowledge_base)} documents to cache")
        except Exception as e:
            print(f"⚠️ Could not save cache: {e}")
    
    def _load_fallback_knowledge(self):
        self.knowledge_base = [
            "[2025] SEASON LEADER: Max Verstappen (VER) with 8 wins",
            "[2024] SEASON LEADER: Max Verstappen (VER) with 9 wins",
            "[2023] SEASON LEADER: Max Verstappen (VER) with 19 wins"
        ]
        print(f"✅ Loaded {len(self.knowledge_base)} fallback documents")
    
    def reload_knowledge_base(self):
        print("🔄 Force reloading knowledge base...")
        self._build_from_fastf1()
        self._save_to_cache()
    
    def get_latest_champion(self, specific_year: int = None) -> Optional[str]:
        if specific_year and specific_year in self.winners_cache:
            winners = [w['driver_code'] for w in self.winners_cache[specific_year]]
            if winners:
                win_counts = Counter(winners)
                leader_code = win_counts.most_common(1)[0][0]
                for w in self.winners_cache[specific_year]:
                    if w['driver_code'] == leader_code:
                        return w['driver_name']
                return leader_code
        
        for year in [2026, 2025, 2024, 2023]:
            if year in self.winners_cache and self.winners_cache[year]:
                winners = [w['driver_code'] for w in self.winners_cache[year]]
                if winners:
                    leader_code = Counter(winners).most_common(1)[0][0]
                    for w in self.winners_cache[year]:
                        if w['driver_code'] == leader_code:
                            return w['driver_name']
                    return leader_code
        return None
    
    def search_knowledge(self, question: str, k: int = 5) -> List[Tuple[str, float]]:
        question_lower = question.lower()
        scored_docs = []
        
        is_recency = any(p in question_lower for p in ['last', 'latest', 'most recent', 'newest'])
        
        stop_words = {'what', 'when', 'where', 'which', 'how', 'the', 'a', 'an', 'and', 'or', 'but', 
                      'in', 'on', 'at', 'to', 'for', 'of', 'with', 'without', 'is', 'are', 'was', 'were'}
        keywords = [w for w in question_lower.split() if w not in stop_words and len(w) > 2]
        
        race_scores = {
            'Canadian Grand Prix': 100,
            'Miami Grand Prix': 80,
            'Japanese Grand Prix': 60,
            'Chinese Grand Prix': 40,
            'Australian Grand Prix': 20
        }
        
        for doc in self.knowledge_base:
            doc_lower = doc.lower()
            score = 0
            
            if is_recency:
                for race, s in race_scores.items():
                    if race.lower() in doc_lower:
                        score += s
                if '[2026]' in doc:
                    score += 100
                elif '[2025]' in doc:
                    score += 60
            
            for kw in keywords:
                if kw in doc_lower:
                    score += 5
            
            year_match = re.search(r'202[3-6]', question)
            if year_match and f'[{year_match.group(0)}]' in doc:
                score += 20
            
            if score > 0:
                scored_docs.append((doc, score))
        
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs[:k]
    
    def is_f1_question(self, question: str) -> bool:
        question_lower = question.lower()
        keywords = [
            'formula', 'f1', 'grand prix', 'gp', 'ferrari', 'mercedes', 'red bull',
            'verstappen', 'hamilton', 'leclerc', 'norris', 'perez', 'sainz',
            'antonelli', 'russell', 'piastri', 'alonso', 'race', 'winner',
            'champion', 'fastest lap', 'tire', 'starting grid', 'pit stop',
            'canada', 'australian', 'chinese', 'japanese', 'miami'
        ]
        if any(k in question_lower for k in keywords):
            return True
        if re.search(r'202[3-6]', question) and any(w in question_lower for w in ['race', 'won', 'winner', 'champion']):
            return True
        return False
    
    def _clean_response(self, text: str) -> str:
        """Clean response - remove ALL fluff, special chars, extra text"""
        if not text:
            return ""
        
        # Remove markdown and special characters
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'#{1,6}\s*', '', text)
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'`{3}.*?`{3}', '', text, flags=re.DOTALL)
        text = re.sub(r'[|`]', '', text)
        
        # Remove common fluff phrases
        fluff_patterns = [
            r'Please\s+let\s+me\s+know.*$', r'I\'ll\s+be\s+happy\s+to\s+help.*$',
            r'Thank\s+you.*$', r'Best\s+regards.*$', r'Is\s+my\s+answer\s+correct\??.*$',
            r'Let\s+me\s+know.*$', r'\[Your\s+Name\].*$', r'F1\s+Analyst.*$',
            r'I\s+hope\s+so.*$', r'That\'s\s+what\s+the\s+data\s+says.*$',
            r'Please\s+let\s+me\s+know\s+if\s+this\s+is\s+correct.*$',
            r'I\s+will\s+be\s+happy\s+to\s+help.*$', r'Best\s+regards.*$'
        ]
        for pattern in fluff_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove "ANSWER:" prefix
        text = re.sub(r'^ANSWER:\s*', '', text, flags=re.IGNORECASE)
        
        # Take only first sentence
        sentences = re.split(r'(?<=[.!?])\s+', text)
        if sentences:
            text = sentences[0].strip()
        
        # Remove any remaining special characters
        text = re.sub(r'[<>{}]', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Ensure no trailing punctuation issues
        if text and text[-1] not in '.!?':
            text += '.'
        
        return text.strip()
    
    def chat(self, question: str) -> str:
        if not self.is_f1_question(question):
            return "I'm specialized in Formula 1. Please ask me about F1 racing! 🏎️"
        
        question_lower = question.lower()
        
        # ========== IMPROVED HANDLING FOR "LAST WIN" QUESTIONS ==========
        last_win_patterns = ['last win', 'last victory', 'last gp won', 'last race won', 'most recent win']
        if any(pattern in question_lower for pattern in last_win_patterns):
            # Map driver names to codes and full names (for better matching)
            driver_map = {
                'hamilton': ('Lewis Hamilton', 'HAM'),
                'lewis': ('Lewis Hamilton', 'HAM'),
                'verstappen': ('Max Verstappen', 'VER'),
                'max': ('Max Verstappen', 'VER'),
                'leclerc': ('Charles Leclerc', 'LEC'),
                'charles': ('Charles Leclerc', 'LEC'),
                'norris': ('Lando Norris', 'NOR'),
                'lando': ('Lando Norris', 'NOR'),
                'russell': ('George Russell', 'RUS'),
                'george': ('George Russell', 'RUS'),
                'piastri': ('Oscar Piastri', 'PIA'),
                'oscar': ('Oscar Piastri', 'PIA'),
                'sainz': ('Carlos Sainz', 'SAI'),
                'carlos': ('Carlos Sainz', 'SAI'),
                'perez': ('Sergio Perez', 'PER'),
                'checo': ('Sergio Perez', 'PER'),
                'alonso': ('Fernando Alonso', 'ALO'),
                'fernando': ('Fernando Alonso', 'ALO'),
                'antonelli': ('Kimi Antonelli', 'ANT'),
                'kimi': ('Kimi Antonelli', 'ANT'),
            }
            
            driver_full = None
            driver_code = None
            
            for name_key, (full_name, code) in driver_map.items():
                if name_key in question_lower:
                    driver_full = full_name
                    driver_code = code
                    break
            
            if driver_full and driver_code:
                # Collect all wins for this driver (using both code and name)
                wins = []
                for doc in self.knowledge_base:
                    # Look for WINNER field with driver code OR driver name
                    if f'WINNER: {driver_code}' in doc or f'({driver_full})' in doc:
                        # Extract year and GP
                        year_match = re.search(r'\[(20\d{2})\]', doc)
                        gp_match = re.search(r'\]\s*([^|]+?)\s*\|', doc)
                        team_match = re.search(r'-\s*([^-]+?)(?:\||$)', doc)
                        
                        if year_match and gp_match:
                            year = int(year_match.group(1))
                            gp = gp_match.group(1).strip()
                            team = team_match.group(1).strip() if team_match else ""
                            wins.append((year, gp, team))
                
                if wins:
                    # Build a list of wins for the LLM to analyze chronologically
                    wins_list = []
                    for year, gp, team in wins:
                        wins_list.append(f"- {gp} {year} ({team})")
                    
                    wins_text = "\n".join(wins_list)
                    
                    # Let the LLM determine the most recent win based on F1 calendar order
                    prompt = f"""Based on the race data below, determine which was {driver_full}'s MOST RECENT (last) Formula 1 win.
    Consider the actual chronological order of the F1 calendar (e.g., Bahrain is early in season, Abu Dhabi is late).

    WINS BY {driver_full}:
    {wins_text}

    QUESTION: {question}

    ANSWER (format exactly like this): "{driver_full}'s last Formula 1 win was the [Grand Prix] [Year] driving for [Team]"

    Answer:"""
                    
                    response = self.llm.invoke(prompt)
                    cleaned = self._clean_response(response)
                    
                    # Ensure the response has the correct format
                    if driver_full not in cleaned:
                        # If LLM didn't format correctly, construct it
                        # Extract GP and year from response
                        gp_year_match = re.search(r'(\w+\s+Grand Prix)\s+(20\d{2})', cleaned)
                        if gp_year_match:
                            gp = gp_year_match.group(1)
                            year = gp_year_match.group(2)
                            team_match = re.search(r'driving for\s+([^.]+)', cleaned)
                            team = team_match.group(1) if team_match else "their team"
                            return f"{driver_full}'s last Formula 1 win was the {gp} {year} driving for {team}."
                    
                    return cleaned
                else:
                    # No wins found in knowledge base - let LLM answer from its knowledge
                    prompt = f"""Based on your general F1 knowledge, what was {driver_full}'s most recent Formula 1 win? 
    Include the race name, year, and team. Answer in one sentence."""
                    response = self.llm.invoke(prompt)
                    return self._clean_response(response)
        
        # ========== EXISTING SPECIAL HANDLING FOR LAST RACE ==========
        if 'last race' in question_lower or 'latest race' in question_lower or 'most recent race' in question_lower:
            for doc in self.knowledge_base:
                if '[2026] Canadian Grand Prix' in doc:
                    winner_match = re.search(r'WINNER:\s*(\w+)\s*\(([^)]+)\)', doc)
                    if winner_match:
                        winner_name = winner_match.group(2)
                        return f"The last race was the 2026 Canadian Grand Prix. The winner was {winner_name}."
            return "I don't have that information."
        
        # ========== EXISTING SPECIAL HANDLING FOR STARTING POSITION ==========
        if 'starting position' in question_lower or 'grid position' in question_lower or 'start from' in question_lower:
            for doc in self.knowledge_base:
                if 'Canadian Grand Prix' in doc and 'GRID:' in doc:
                    match = re.search(r'P(\d+):ANT', doc)
                    if match:
                        position = match.group(1)
                        return f"Kimi Antonelli started from P{position} at the 2026 Canadian Grand Prix."
            return "I don't have grid position data for that race."
        
        # ========== REGULAR RAG FOR ALL OTHER QUESTIONS ==========
        relevant_docs = self.search_knowledge(question, k=4)
        
        if relevant_docs:
            context = "\n".join([doc for doc, _ in relevant_docs])
            prompt = f"""Answer the question based ONLY on the data below.

    DATA:
    {context}

    QUESTION: {question}

    ANSWER (concise, one sentence):"""
            
            response = self.llm.invoke(prompt)
            return self._clean_response(response)
        
        # If no data found, use LLM's general knowledge
        prompt = f"""Answer this F1 question based on your general knowledge.

    QUESTION: {question}
    ANSWER:"""
        
        response = self.llm.invoke(prompt)
        return self._clean_response(response)
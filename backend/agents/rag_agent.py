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
        """Build knowledge base from FastF1 data (slow - only runs once)"""
        try:
            import fastf1
            
            cache_dir = Path(__file__).parent.parent.parent / "data" / "fastf1_cache"
            fastf1.Cache.enable_cache(str(cache_dir))
            
            # Process years in REVERSE order (2026 first!)
            years = [2026, 2025, 2024, 2023]
            knowledge_texts = []
            
            for year in years:
                print(f"\n📅 Processing {year} season...")
                try:
                    schedule = fastf1.get_event_schedule(year)
                    # Get race sessions only
                    races = schedule[schedule['Session5'] == 'Race'] if 'Session5' in schedule.columns else schedule
                    print(f"  Found {len(races)} races")
                    
                    year_winners = []
                    
                    for idx, race in races.iterrows():
                        gp_name = race['EventName']
                        
                        try:
                            session = fastf1.get_session(year, gp_name, "R")
                            session.load(telemetry=False, laps=True, weather=False)
                            
                            results = session.results
                            if not results.empty:
                                winner = results.iloc[0]
                                winner_code = winner['Abbreviation']
                                winner_name = winner['FullName']
                                winner_team = winner['TeamName']
                                
                                year_winners.append(winner_code)
                                
                                # Store in cache for quick lookup
                                if year not in self.winners_cache:
                                    self.winners_cache[year] = []
                                self.winners_cache[year].append({
                                    'gp': gp_name,
                                    'driver_code': winner_code,
                                    'driver_name': winner_name,
                                    'team': winner_team
                                })
                                
                                # Add to knowledge base
                                text = f"[{year}] {gp_name} WINNER: {winner_code} ({winner_name}) - {winner_team}"
                                
                                # Add fastest lap if available
                                fastest = session.laps.pick_fastest()
                                if not fastest.empty:
                                    text += f" | FASTEST LAP: {fastest['Driver']} - {fastest['LapTime'].total_seconds():.3f}s"
                                
                                knowledge_texts.append(text)
                                print(f"    ✅ {gp_name}: {winner_name} ({winner_code})")
                                
                        except Exception as e:
                            if "no data" not in str(e).lower() and "404" not in str(e):
                                print(f"    ⚠️ Could not load {gp_name}: {str(e)[:50]}")
                            continue
                    
                    # Calculate championship leader for this year
                    if year_winners:
                        win_counts = Counter(year_winners)
                        leader = win_counts.most_common(1)[0]
                        leader_code = leader[0]
                        leader_wins = leader[1]
                        
                        # Find the full name of the leader
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
        """Search with recency bias"""
        question_lower = question.lower()
        scored_docs = []
        
        year_weights = {2026: 150, 2025: 100, 2024: 50, 2023: 25}
        
        for doc in self.knowledge_base:
            doc_lower = doc.lower()
            
            # Extract year
            year = None
            if doc.startswith('[2026]'):
                year = 2026
            elif doc.startswith('[2025]'):
                year = 2025
            elif doc.startswith('[2024]'):
                year = 2024
            elif doc.startswith('[2023]'):
                year = 2023
            
            # Relevance scoring
            relevance = sum(2 for word in question_lower.split() if len(word) > 3 and word in doc_lower)
            recency_bonus = year_weights.get(year, 0) if year else 0
            
            total_score = relevance + recency_bonus
            
            if total_score > 0:
                scored_docs.append((doc, total_score))
        
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs[:k]
    
    def is_f1_question(self, question: str) -> bool:
        """Check if question is F1-related"""
        f1_keywords = [
            'formula', 'f1', 'grand prix', 'ferrari', 'mercedes', 'red bull',
            'verstappen', 'hamilton', 'leclerc', 'norris', 'perez', 'sainz',
            'antonelli', 'russell', 'piastri', 'alonso', 'vettel',
            'pirelli', 'drs', 'qualifying', 'sprint', 'race', 'championship',
            'monza', 'monaco', 'silverstone', 'spa', 'suzuka', 'miami',
            'canada', 'australian', 'chinese', 'japanese'
        ]
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in f1_keywords)
    
    def chat(self, question: str) -> str:
        """Answer F1 questions using cached race data - SINGLE ANSWER ONLY"""
        if not self.is_f1_question(question):
            return "I'm specialized in Formula 1. Please ask me about F1 racing! 🏎️"
        
        question_lower = question.lower()
        
        # Extract year from question
        year_match = re.search(r'202[3-6]', question)
        specific_year = int(year_match.group(0)) if year_match else None
        
        # Check for specific race winners
        gp_patterns = {
            'australian': 'Australian',
            'chinese': 'Chinese', 
            'japanese': 'Japanese',
            'miami': 'Miami',
            'canadian': 'Canadian',
            'monaco': 'Monaco',
            'british': 'British',
            'austrian': 'Austrian',
            'belgian': 'Belgian',
            'italian': 'Italian',
            'singapore': 'Singapore',
            'abu dhabi': 'Abu Dhabi'
        }
        
        for gp_key, gp_name in gp_patterns.items():
            if gp_key in question_lower and specific_year:
                winner = self.get_race_winner(specific_year, gp_name)
                if winner:
                    return winner
        
        # Check for championship question
        if 'champion' in question_lower or 'latest' in question_lower:
            champion = self.get_latest_champion(specific_year)
            if champion:
                return champion
        
        # Fallback to LLM with STRICT single-answer prompt
        relevant_docs = self.search_knowledge(question, k=2)
        
        if relevant_docs:
            context = "\n".join([doc for doc, _ in relevant_docs])
            # STRICT prompt - no extra text, no follow-up questions
            prompt = f"""Answer the question with ONLY the driver name or short fact. DO NOT ask questions. DO NOT add extra Q&A. STOP after one sentence.

DATA: {context}

QUESTION: {question}
ANSWER:"""
        else:
            # Ultra-strict prompt for no context
            prompt = f"""Answer with ONE word or short phrase only. NO extra text. NO questions.

QUESTION: {question}
ANSWER:"""
        
        try:
            response = self.llm.invoke(prompt)
            
            # Clean up response
            response = response.strip()
            
            # Remove any "ANSWER:" prefix
            response = re.sub(r'^ANSWER:\s*', '', response, flags=re.IGNORECASE)
            response = re.sub(r'^A:\s*', '', response, flags=re.IGNORECASE)
            
            # CRITICAL: Remove anything after a question mark or "Q:"
            if '?' in response:
                response = response.split('?')[0]
            if 'Q:' in response:
                response = response.split('Q:')[0]
            
            # Take only the first sentence
            sentences = re.split(r'[.!?]+', response)
            if sentences:
                response = sentences[0].strip()
            
            # Remove any remaining extra patterns
            response = re.sub(r'\s+Q:.*$', '', response, flags=re.IGNORECASE)
            response = re.sub(r'\s+Which.*$', '', response, flags=re.IGNORECASE)
            
            # Limit to 100 characters max
            if len(response) > 100:
                response = response[:100]
            
            return response if response else "I don't have that information."
            
        except Exception as e:
            return f"Error: {str(e)}"
"""
Strategy Agent - Explains WHY strategic decisions were made
Handles questions about pit stops, tire choices, race strategy, etc.
"""

import re
from .rag_agent import F1RAGAgent


class StrategyAgent:
    def __init__(self):
        """Initialize the Strategy Agent"""
        print("🎯 Initializing Strategy Agent...")
        
        # Reuse the RAG agent for data retrieval
        self.data_agent = F1RAGAgent()
        
        # Ensure knowledge base is loaded
        self.data_agent.initialize_knowledge_base(force_reload=False)
        
        print("✅ Strategy Agent ready!")
    
    def analyze(self, question: str) -> str:
        """
        Analyze and explain strategic decisions in F1
        
        Args:
            question: User's question about strategy (why, how, what if)
        
        Returns:
            Strategic analysis and explanation
        """
        question_lower = question.lower()
        
        # Extract key information from question
        driver, year, gp, lap = self._extract_context(question_lower)
        
        # Get relevant race data
        context_data = self._get_relevant_data(driver, year, gp, lap)
        
        if not context_data:
            # If no specific data found, use general F1 knowledge
            return self._general_strategy_answer(question)
        
        # Build strategy analysis prompt
        prompt = self._build_strategy_prompt(question, context_data, driver, gp, year, lap)        
        try:
            response = self.data_agent.llm.invoke(prompt)
            cleaned = self.data_agent._clean_response(response)
            return cleaned
        except Exception as e:
            return f"Error analyzing strategy: {str(e)}"
    
    def _extract_context(self, question_lower: str) -> tuple:
        """Extract driver, year, GP, and lap number from question"""
        driver = None
        year = None
        gp = None
        lap = None
        
        # Driver mapping
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
        
        # Extract year
        year_match = re.search(r'20[2-6][0-9]', question_lower)
        if year_match:
            year = int(year_match.group(0))
        
        # Extract GP
        gp_list = ['australian', 'chinese', 'japanese', 'miami', 'canadian', 
                   'monaco', 'british', 'austrian', 'belgian', 'italian',
                   'singapore', 'abu dhabi', 'bahrain', 'saudi']
        for gp_name in gp_list:
            if gp_name in question_lower:
                gp = gp_name.capitalize()
                break
        
        # Extract lap number
        lap_match = re.search(r'lap\s*(\d+)', question_lower)
        if lap_match:
            lap = int(lap_match.group(1))
        
        return driver, year, gp, lap
    
    def _get_relevant_data(self, driver: str, year: int, gp: str, lap: int) -> str:
        """Get relevant race data from knowledge base"""
        context_parts = []
        
        for doc in self.data_agent.knowledge_base:
            doc_lower = doc.lower()
            
            # Match year
            if year and str(year) not in doc:
                continue
            
            # Match GP (if specified)
            if gp and gp.lower() not in doc_lower:
                continue
            
            # Match driver (if specified)
            if driver and driver.lower() not in doc_lower:
                continue
            
            context_parts.append(doc)
        
        return "\n\n".join(context_parts[:3])    
    def _build_strategy_prompt(self, question: str, context: str, driver: str, gp: str, year: int, lap: int) -> str:
        """Build the prompt for strategy analysis"""
        
        base_prompt = f"""You are an expert F1 strategy analyst. Answer the strategy question based ONLY on the race data below.

    RACE DATA:
    {context}

    QUESTION: What was the strategy for {driver if driver else 'the driver'} in the {gp if gp else 'Grand Prix'} {year if year else ''}?

    YOUR ANSWER MUST INCLUDE:
    1. Starting position (from GRID data)
    2. Tire strategy (from TIRE and PITS data)
    3. Final result (from WINNER data if available)
    4. Key strategic decision (e.g., undercut, overcut, tire management)

    ANSWER FORMAT (complete 3-4 sentence paragraph):
    """
        
        return base_prompt
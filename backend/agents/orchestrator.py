"""
Orchestrator Agent - Routes questions to specialized agents with memory
"""

from .strategy_agent import StrategyAgent
from .comparison_agent import ComparisonAgent
from .memory_agent import MemoryAgent


class Orchestrator:
    def __init__(self):
        """Initialize the orchestrator with all available agents"""
        print("🚀 Initializing Orchestrator...")
        
        # Import your existing RAG agent
        from .rag_agent import F1RAGAgent
        
        # Initialize all agents
        self.data_agent = F1RAGAgent()
        self.strategy_agent = StrategyAgent()
        self.comparison_agent = ComparisonAgent()
        self.memory_agent = MemoryAgent()
        
        # Initialize knowledge base
        print("📚 Loading knowledge base...")
        self.data_agent.initialize_knowledge_base(force_reload=False)
        
        print(f"📊 Knowledge base loaded: {len(self.data_agent.knowledge_base)} documents")
        print("✅ Orchestrator ready with Data Agent, Strategy Agent, Comparison Agent, and Memory Agent!")
    
    def route(self, question: str) -> str:
        """Send the question to the right agent based on question type"""
        question_lower = question.lower()
        
        # Handle memory-related commands
        if 'clear memory' in question_lower or 'forget context' in question_lower:
            self.memory_agent.clear_session()
            return "🧠 Session memory cleared! I've forgotten our previous conversation."
        
        if 'conversation summary' in question_lower or 'what did we discuss' in question_lower:
            return f"🧠 {self.memory_agent.get_conversation_summary()}"
        
        if 'memory stats' in question_lower:
            stats = self.memory_agent.get_stats()
            return f"🧠 **Memory Statistics**\n\n• Conversation length: {stats['conversation_length']} exchanges\n• Last driver: {stats['last_driver']}\n• Last GP: {stats['last_gp']}\n• Last year: {stats['last_year']}"
        
        # FIRST: Check for teammate questions BEFORE enhancing
        # This ensures we catch "who was his teammate?" type questions
        teammate_indicators = ['teammate', 'team mate', 'team-mate', 'his teammate', 'her teammate', 'their teammate']
        is_teammate_question = any(indicator in question_lower for indicator in teammate_indicators)
        
        if is_teammate_question:
            # Check if we have a driver in memory
            if self.memory_agent.session_memory['current_session'].get('last_driver'):
                print(f"👥 Teammate question detected directly in orchestrator")
                result = self.memory_agent.get_teammate_answer(question)
                self.memory_agent.update_memory(question, result)
                return result
            else:
                return "I don't know which driver you're asking about. Please ask about a specific driver first, like 'Who won the Japanese GP 2026?'"
        
        # Enhance question with memory for other types of follow-ups
        enhanced_question = self.memory_agent.enhance_question(question)
        
        # Weather questions
        weather_keywords = [
            'weather', 'rain', 'wet', 'dry', 'temperature', 'humidity',
            'conditions', 'forecast', 'how was the weather', 'weather like',
            'air temp', 'track temp', 'rainfall'
        ]
        if any(keyword in question_lower for keyword in weather_keywords):
            print(f"🌤️ [Weather Question] Routing to Strategy Agent")
            result = self._handle_strategy_question(enhanced_question)
            self.memory_agent.update_memory(question, result)
            return result
        
        # Comparison questions
        comparison_keywords = ['compare', 'vs', 'versus', 'difference between', 'faster', 'better']
        if any(keyword in question_lower for keyword in comparison_keywords):
            print(f"⚖️ [Comparison Question] Routing to Comparison Agent")
            result = self._handle_comparison_question(enhanced_question)
            self.memory_agent.update_memory(question, result)
            return result
        
        # Strategy questions
        strategy_keywords = ['why', 'strategy', 'decision', 'pit', 'tire choice', 
                            'reason', 'explain', 'how did', 'what strategy']
        if any(keyword in question_lower for keyword in strategy_keywords):
            print(f"🎯 [Strategy Question] Routing to Strategy Agent")
            result = self._handle_strategy_question(enhanced_question)
            self.memory_agent.update_memory(question, result)
            return result
        
        # DEFAULT: Data Agent for factual questions
        print(f"📊 [Data Question] Routing to Data Agent")
        result = self._handle_data_question(enhanced_question)
        self.memory_agent.update_memory(question, result)
        return result
    
    def _handle_data_question(self, question: str) -> str:
        """Handle factual questions using the Data Agent"""
        print(f"📊 [Data Agent] Processing: {question[:50]}...")
        return self.data_agent.chat(question)
    
    def _handle_strategy_question(self, question: str) -> str:
        """Handle strategy questions using the Strategy Agent"""
        print(f"🎯 [Strategy Agent] Processing: {question[:50]}...")
        return self.strategy_agent.analyze(question)
    
    def _handle_comparison_question(self, question: str) -> str:
        """Handle comparison questions using the Comparison Agent"""
        print(f"⚖️ [Comparison Agent] Processing: {question[:50]}...")
        return self.comparison_agent.compare(question)
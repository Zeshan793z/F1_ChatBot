"""
Orchestrator Agent - Routes questions to specialized agents
"""

from .strategy_agent import StrategyAgent
from .comparison_agent import ComparisonAgent  # ADD THIS


class Orchestrator:
    def __init__(self):
        """Initialize the orchestrator with all available agents"""
        print("🚀 Initializing Orchestrator...")
        
        # Import your existing RAG agent
        from .rag_agent import F1RAGAgent
        
        # Initialize all agents
        self.data_agent = F1RAGAgent()
        self.strategy_agent = StrategyAgent()
        self.comparison_agent = ComparisonAgent()  # NEW
        
        # Initialize knowledge base
        print("📚 Loading knowledge base...")
        self.data_agent.initialize_knowledge_base(force_reload=False)
        
        print(f"📊 Knowledge base loaded: {len(self.data_agent.knowledge_base)} documents")
        print("✅ Orchestrator ready with Data Agent, Strategy Agent, and Comparison Agent!")
    
    def route(self, question: str) -> str:
        """Send the question to the right agent based on question type"""
        question_lower = question.lower()
        
        # Comparison questions go to Comparison Agent (HIGHEST PRIORITY)
        comparison_keywords = ['compare', 'vs', 'versus', 'difference between', 'faster', 'better']
        if any(keyword in question_lower for keyword in comparison_keywords):
            return self._handle_comparison_question(question)
        
        # Strategy questions go to Strategy Agent
        strategy_keywords = ['why', 'strategy', 'decision', 'pit', 'tire choice', 
                            'reason', 'explain', 'how did', 'what strategy']
        if any(keyword in question_lower for keyword in strategy_keywords):
            return self._handle_strategy_question(question)
        
        # DEFAULT: Data Agent for factual questions
        return self._handle_data_question(question)
    
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
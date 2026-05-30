"""
Orchestrator Agent - Routes questions to specialized agents
"""

class Orchestrator:
    def __init__(self):
        """Initialize the orchestrator with all available agents"""
        print("🚀 Initializing Orchestrator...")
        
        # Import your existing RAG agent
        from .rag_agent import F1RAGAgent
        
        # Create the agent
        self.data_agent = F1RAGAgent()
        
        # IMPORTANT: Initialize the knowledge base
        print("📚 Loading knowledge base...")
        self.data_agent.initialize_knowledge_base(force_reload=False)
        
        # Verify knowledge base loaded
        print(f"📊 Knowledge base loaded: {len(self.data_agent.knowledge_base)} documents")
        print(f"🏆 Winners cache: {len(self.data_agent.winners_cache)} seasons")
        
        print("✅ Orchestrator ready!")
    
    def route(self, question: str) -> str:
        """
        Send the question to the right agent based on question type
        """
        question_lower = question.lower()
        
        # Strategy questions (WHY, HOW, strategy analysis)
        strategy_keywords = ['why', 'strategy', 'decision', 'pit', 'tire choice', 'reason']
        if any(keyword in question_lower for keyword in strategy_keywords):
            return self._handle_strategy_question(question)
        
        # Comparison questions (compare X vs Y)
        comparison_keywords = ['compare', 'vs', 'versus', 'difference between']
        if any(keyword in question_lower for keyword in comparison_keywords):
            return self._handle_comparison_question(question)
        
        # Visualization questions (charts, graphs)
        visual_keywords = ['chart', 'graph', 'plot', 'visualize', 'show me']
        if any(keyword in question_lower for keyword in visual_keywords):
            return self._handle_visual_question(question)
        
        # DEFAULT: All other questions go to Data Agent (your working RAG agent)
        return self._handle_data_question(question)
    
    def _handle_data_question(self, question: str) -> str:
        """Handle factual questions using the Data Agent (your working RAG agent)"""
        print(f"📊 Routing to Data Agent: {question[:50]}...")
        
        # DIRECTLY call the same method that works
        return self.data_agent.chat(question)
    
    def _handle_strategy_question(self, question: str) -> str:
        """Handle strategy questions - uses Data Agent for now"""
        print(f"🎯 Strategy question: {question[:50]}...")
        # For now, use Data Agent
        return self.data_agent.chat(question)
    
    def _handle_comparison_question(self, question: str) -> str:
        """Handle comparison questions - uses Data Agent for now"""
        print(f"⚖️ Comparison question: {question[:50]}...")
        return self.data_agent.chat(question)
    
    def _handle_visual_question(self, question: str) -> str:
        """Handle visualization questions"""
        print(f"📊 Visualization question: {question[:50]}...")
        return "🔜 Chart visualization feature is coming soon! For now:\n\n" + self.data_agent.chat(question)
"""
OmniSynth - Research Agent
Specialized agent for literature discovery and semantic research
"""
from typing import Dict, Any, List, Optional
from app.services.groq_service import groq_service
from app.services.hyde_service import hyde_service
from loguru import logger


class ResearchAgent:
    """AI Research Agent for literature discovery and analysis."""

    async def search_literature(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """Search for relevant literature using HyDE-enhanced RAG."""
        try:
            results = await hyde_service.search_with_hyde(query, top_k=top_k, use_hyde=True)
            return results
        except Exception as e:
            logger.error(f"Literature search failed: {e}")
            return {"query": query, "results": [], "error": str(e)}

    async def analyze_research_gap(self, topic: str, context: str = "") -> str:
        """Identify research gaps in a topic."""
        system_prompt = """You are an expert academic researcher. Analyze the given topic 
        and identify key research gaps, unexplored areas, and opportunities for novel contribution.
        Structure your response clearly with: current state, identified gaps, and research opportunities."""
        
        messages = [{
            "role": "user",
            "content": f"Topic: {topic}\n\nContext: {context[:1000] if context else 'None'}\n\nAnalyze research gaps:"
        }]
        return await groq_service.generate(messages, system_prompt=system_prompt, max_tokens=1500)

    async def generate_research_plan(self, topic: str) -> str:
        """Generate a comprehensive research plan."""
        system_prompt = """You are an expert academic research advisor. Create a detailed, 
        structured research plan with clear phases, methodologies, and timelines."""
        
        messages = [{
            "role": "user",
            "content": f"Create a comprehensive research plan for: {topic}"
        }]
        return await groq_service.generate(messages, system_prompt=system_prompt, max_tokens=2000)

    async def summarize_paper(self, text: str, focus: str = "") -> Dict[str, str]:
        """Summarize an academic paper with structured output."""
        system_prompt = """You are an expert at summarizing academic papers. 
        Provide structured summaries with: Objective, Methods, Results, Conclusions, and Key Contributions."""
        
        prompt = f"{'Focus on: ' + focus + chr(10) if focus else ''}Summarize this paper:\n\n{text[:4000]}"
        messages = [{"role": "user", "content": prompt}]
        summary = await groq_service.generate(messages, system_prompt=system_prompt, max_tokens=1000)
        
        keywords = await groq_service.extract_keywords(text)
        return {"summary": summary, "keywords": keywords}

    async def answer_research_query(
        self,
        query: str,
        history: List[Dict[str, str]] = None,
        use_hyde: bool = True,
    ) -> Dict[str, Any]:
        """Answer a research query using RAG pipeline."""
        return await hyde_service.augmented_generation(
            query=query,
            conversation_history=history or [],
            use_hyde=use_hyde,
        )

    async def generate_methodology(self, research_question: str, field: str = "") -> str:
        """Generate research methodology section."""
        system_prompt = """You are an expert in research design and methodology. 
        Generate a detailed, academically rigorous methodology section."""
        messages = [{
            "role": "user",
            "content": f"Research Question: {research_question}\nField: {field}\n\nGenerate a detailed methodology:"
        }]
        return await groq_service.generate(messages, system_prompt=system_prompt, max_tokens=1500)


research_agent = ResearchAgent()

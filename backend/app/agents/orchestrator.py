"""
OmniSynth - Multi-Agent Orchestrator
LangGraph-powered multi-agent routing and coordination
"""
from typing import Dict, Any, Optional, List
from app.agents.research_agent import research_agent
from app.services.groq_service import groq_service
from app.services.plagiarism_service import plagiarism_service
from app.services.citation_service import citation_service
from app.services.ocr_service import ocr_service
from app.services.hyde_service import hyde_service
from loguru import logger
import asyncio


class AgentOrchestrator:
    """
    Multi-Agent Orchestrator using intent-based routing.
    Routes queries to specialized agents based on intent classification.
    """

    AGENT_TYPES = {
        "research": "Research & Literature Agent",
        "ocr": "OCR & Document Agent",
        "citation": "Citation & Reference Agent",
        "drafting": "Academic Drafting Agent",
        "summarization": "Summarization Agent",
        "plagiarism": "Plagiarism Detection Agent",
        "recommendation": "Research Recommendation Agent",
        "productivity": "Productivity Analytics Agent",
        "general": "General AI Assistant",
    }

    async def classify_intent(self, query: str) -> str:
        """Classify user query to determine which agent to route to."""
        query_lower = query.lower()
        
        # Rule-based fast classification
        if any(kw in query_lower for kw in ["cite", "citation", "reference", "bibliography", "apa", "mla", "ieee"]):
            return "citation"
        if any(kw in query_lower for kw in ["plagiarism", "originality", "similarity check"]):
            return "plagiarism"
        if any(kw in query_lower for kw in ["summarize", "summary", "abstract", "tldr"]):
            return "summarization"
        if any(kw in query_lower for kw in ["write", "draft", "compose", "introduction", "conclusion", "methodology"]):
            return "drafting"
        if any(kw in query_lower for kw in ["ocr", "extract text", "scan", "document processing"]):
            return "ocr"
        if any(kw in query_lower for kw in ["recommend", "suggest", "find papers", "literature", "research gap"]):
            return "research"
        if any(kw in query_lower for kw in ["analytics", "productivity", "progress", "statistics"]):
            return "productivity"

        # AI-based classification for complex queries
        try:
            prompt = f"""Classify this query into exactly one category:
research, citation, drafting, summarization, plagiarism, recommendation, ocr, productivity, general

Query: "{query}"

Reply with ONLY the category name."""
            messages = [{"role": "user", "content": prompt}]
            response = await groq_service.generate(
                messages, model=groq_service.fast_model, max_tokens=20, temperature=0.1
            )
            category = response.strip().lower().split()[0] if response else "general"
            return category if category in self.AGENT_TYPES else "general"
        except Exception:
            return "general"

    async def route_and_execute(
        self,
        query: str,
        agent_type: Optional[str] = None,
        context: Dict[str, Any] = None,
        conversation_history: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Route query to appropriate agent and execute."""
        if not agent_type:
            agent_type = await self.classify_intent(query)

        logger.info(f"Routing to agent: {agent_type} | Query: {query[:80]}")
        context = context or {}
        history = conversation_history or []

        try:
            if agent_type == "research":
                result = await research_agent.answer_research_query(query, history)
                return {**result, "agent": "research"}

            elif agent_type == "citation":
                # Extract citation data from query context
                data = context.get("citation_data", {"title": query, "authors": [], "year": "2024"})
                style = context.get("style", "APA")
                formatted = await citation_service.generate_citation(style, data)
                return {
                    "answer": f"Here is your {style} citation:\n\n{formatted['formatted']}\n\nBibTeX:\n{formatted['bibtex']}",
                    "citation": formatted,
                    "agent": "citation",
                    "model_used": "citation_service",
                }

            elif agent_type == "summarization":
                text = context.get("text", query)
                summary = await groq_service.summarize_text(text)
                return {
                    "answer": summary,
                    "agent": "summarization",
                    "model_used": groq_service.fast_model,
                }

            elif agent_type == "drafting":
                content_type = context.get("content_type", "paragraph")
                topic = context.get("topic", query)
                word_limit = context.get("word_limit", 500)
                draft = await groq_service.generate_content(content_type, topic, word_limit=word_limit)
                return {
                    "answer": draft,
                    "agent": "drafting",
                    "model_used": groq_service.primary_model,
                }

            elif agent_type == "plagiarism":
                text = context.get("text", query)
                report = await plagiarism_service.check_plagiarism(text)
                return {
                    "answer": f"Plagiarism check complete. Originality score: {report['overall_score']}%\n\n{report.get('summary', '')}",
                    "report": report,
                    "agent": "plagiarism",
                    "model_used": "plagiarism_service",
                }

            elif agent_type == "recommendation":
                results = await research_agent.search_literature(query, top_k=5)
                answer = f"Found {results.get('total_results', 0)} relevant papers for your query."
                return {
                    "answer": answer,
                    "sources": results.get("results", []),
                    "agent": "recommendation",
                    "model_used": groq_service.primary_model,
                }

            else:  # general
                result = await hyde_service.augmented_generation(
                    query=query,
                    conversation_history=history,
                    use_hyde=False,
                )
                return {**result, "agent": "general"}

        except Exception as e:
            logger.error(f"Agent execution failed for {agent_type}: {e}")
            fallback = await groq_service.generate(
                [{"role": "user", "content": query}],
                system_prompt="You are OmniSynth AI assistant. Help the user with their research query.",
            )
            return {
                "answer": fallback,
                "agent": "general",
                "model_used": groq_service.primary_model,
                "error": str(e),
            }

    async def multi_agent_pipeline(
        self,
        query: str,
        agents: List[str],
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Run multiple agents in parallel and aggregate results."""
        tasks = [
            self.route_and_execute(query, agent_type=agent, context=context)
            for agent in agents
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        combined = {}
        for agent, result in zip(agents, results):
            if isinstance(result, Exception):
                combined[agent] = {"error": str(result)}
            else:
                combined[agent] = result
        return combined


orchestrator = AgentOrchestrator()

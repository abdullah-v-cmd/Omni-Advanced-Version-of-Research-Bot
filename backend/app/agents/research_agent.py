"""
OmniSynth - Research Agent
Specialized agent for literature discovery and semantic research
"""
import re
import inspect
import asyncio
from typing import Dict, Any, List, Optional
from app.services.groq_service import groq_service
from app.services.hyde_service import hyde_service
from loguru import logger


class ResearchAgent:
    """AI Research Agent for literature discovery and analysis."""

    async def search_literature(self, query: str, top_k: int = 10, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Search for relevant literature using HyDE-enhanced RAG, preserving conversational context safely."""
        try:
            search_kwargs = {"query": query, "top_k": top_k, "use_hyde": True}
            sig = inspect.signature(hyde_service.search_with_hyde)
            if "conversation_history" in sig.parameters:
                search_kwargs["conversation_history"] = conversation_history
            else:
                logger.warning("⚠️ hyde_service.search_with_hyde does not accept conversation_history. Falling back to query-only.")

            results = await hyde_service.search_with_hyde(**search_kwargs)
            return results
        except Exception as e:
            logger.error(f"Literature search failed: {e}")
            return {"query": query, "results": [], "error": str(e)}

    async def analyze_research_gap(self, topic: str, context: str = "") -> str:
        """Identify research gaps in a topic."""
        system_prompt = """You are an expert academic researcher. Analyze the given topic 
        and identify key research gaps, unexplored areas, and opportunities for novel contribution."""
        
        messages = [{"role": "user", "content": f"Topic: {topic}\n\nContext: {context[:1000] if context else 'None'}\n\nAnalyze research gaps:"}]
        return await groq_service.generate(messages, system_prompt=system_prompt, max_tokens=1500)

    async def generate_research_plan(self, topic: str) -> str:
        """Generate a comprehensive research plan."""
        system_prompt = """You are an expert academic research advisor. Create a detailed, 
        structured research plan with clear phases, methodologies, and timelines."""
        
        messages = [{"role": "user", "content": f"Create a comprehensive research plan for: {topic}"}]
        return await groq_service.generate(messages, system_prompt=system_prompt, max_tokens=2000)

    async def summarize_paper(self, text: str, focus: str = "") -> Dict[str, Any]:
        """Summarize an academic paper with structured output concurrently."""
        system_prompt = """You are an expert at summarizing academic papers. 
        Provide structured summaries with: Objective, Methods, Results, Conclusions, and Key Contributions."""
        
        truncated_text = text[:4000] if text else ""
        messages = [{"role": "user", "content": f"Focus on: {focus}\n" if focus else "" + f"Summarize this paper:\n\n{truncated_text}"}]
        
        try:
            summary_task = groq_service.generate(messages=messages, system_prompt=system_prompt, max_tokens=1000)
            keyword_task = groq_service.extract_keywords(truncated_text)
            summary, keywords = await asyncio.gather(summary_task, keyword_task)
            return {"summary": summary, "keywords": keywords}
        except Exception as e:
            logger.error(f"Paper summary compilation failed: {e}")
            return {"summary": "Error generating summary.", "keywords": [], "error": str(e)}

    async def answer_research_query(
        self,
        query: str,
        history: List[Dict[str, str]] = None,
        use_hyde: bool = True,
        hyde_rag: bool = False,
    ) -> Dict[str, Any]:
        """Answer a research query routing dynamically between local files and general AI knowledge."""
        
        history_window = (history or [])[-10:]
        clean_history = [
            {"role": m.get("role") if isinstance(m, dict) else getattr(m, "role", "user"),
             "content": m.get("content") if isinstance(m, dict) else getattr(m, "content", "")}
            for m in history_window
        ]
        
        if hyde_rag:
            normalized_query = query.lower()
            number_match = re.search(r'(\d+)\s+research\s+paper', normalized_query)
            count_requested = int(number_match.group(1)) if number_match else 1
            
            is_list_request = any(k in normalized_query for k in ["extract", "give", "list"])
            calculated_k = (max(count_requested, 5) * 4) if (is_list_request or number_match) else 5

            if is_list_request or number_match:
                search_payload = await self.search_literature(query=query, top_k=calculated_k, conversation_history=clean_history)
                source_docs = search_payload.get("results", [])
                
                all_discovered = {}
                for idx, doc in enumerate(source_docs):
                    doc_dict = doc if isinstance(doc, dict) else getattr(doc, "__dict__", {})
                    meta = doc_dict.get("metadata", {}) if isinstance(doc_dict.get("metadata"), dict) else {}
                    key = doc_dict.get("file_name") or meta.get("file_name") or f"src_{idx}"
                    
                    if key not in all_discovered:
                        all_discovered[key] = {"title": doc_dict.get("title") or "Unknown", "snippets": [doc_dict.get("page_content", "")]}
                    elif len(all_discovered[key]["snippets"]) < 2:
                        all_discovered[key]["snippets"].append(doc_dict.get("page_content", ""))

                context_blocks = [f"PAPER {i+1}:\nTitle: {v['title']}\nExcerpt:\n{chr(10).join(v['snippets'])}" for i, (k, v) in enumerate(all_discovered.items())]
                messages = list(clean_history) + [{"role": "user", "content": f"Query: {query}\n\nContext:\n{chr(10).join(context_blocks)}"}]
                
                return {"query": query, "answer": await groq_service.generate(messages=messages, system_prompt="Act as an academic clerk. Format a list."), "source_documents": source_docs}

            return await hyde_service.augmented_generation(query=query, conversation_history=list(clean_history), use_hyde=use_hyde, top_k=calculated_k)

        else:
            messages = list(clean_history) + [{"role": "user", "content": query}]
            return {"query": query, "answer": await groq_service.generate(messages=messages, system_prompt="You are OmniSynth AI.", max_tokens=2048), "source_documents": []}

    async def generate_methodology(self, research_question: str, field: str = "") -> str:
        """Generate research methodology section."""
        return await groq_service.generate([{"role": "user", "content": f"Question: {research_question}\nField: {field}"}], system_prompt="Expert research designer.", max_tokens=1500)

research_agent = ResearchAgent()

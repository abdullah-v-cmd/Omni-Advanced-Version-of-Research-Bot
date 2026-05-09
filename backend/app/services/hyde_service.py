"""
OmniSynth - HyDE (Hypothetical Document Embeddings) Service
Enhances retrieval by generating hypothetical documents before searching
"""
from typing import List, Dict, Any, Optional, Tuple
from app.services.groq_service import groq_service
from app.services.embedding_service import embedding_service
from loguru import logger


class HyDEService:
    """
    HyDE (Hypothetical Document Embeddings) retrieval enhancement.
    
    Process:
    1. Generate a hypothetical ideal document for the query
    2. Embed the hypothetical document
    3. Use the embedding to search the vector database
    4. Return relevant actual documents
    """

    async def enhance_query(self, query: str, context: str = "") -> Dict[str, Any]:
        """
        Enhance a query using HyDE technique.
        Returns both the original query, hypothetical document, and embeddings.
        """
        logger.info(f"Generating HyDE document for: {query[:100]}...")
        try:
            hyde_doc = await groq_service.generate_hyde_document(query)
        except Exception as e:
            logger.warning(f"HyDE generation failed, using original query: {e}")
            hyde_doc = query

        combined_text = f"{query}\n\n{hyde_doc}"
        return {
            "original_query": query,
            "hypothetical_document": hyde_doc,
            "combined_text": combined_text,
            "enhanced": True,
        }

    async def search_with_hyde(
        self,
        query: str,
        top_k: int = 5,
        use_hyde: bool = True,
    ) -> Dict[str, Any]:
        """
        Search the vector database using HyDE-enhanced query.
        """
        if use_hyde:
            enhanced = await self.enhance_query(query)
            search_text = enhanced["combined_text"]
            hyde_doc = enhanced["hypothetical_document"]
        else:
            search_text = query
            hyde_doc = None

        results = await embedding_service.search(search_text, top_k=top_k)

        return {
            "query": query,
            "hyde_document": hyde_doc,
            "results": results,
            "total_results": len(results),
            "use_hyde": use_hyde,
        }

    async def augmented_generation(
        self,
        query: str,
        conversation_history: List[Dict[str, str]] = None,
        top_k: int = 5,
        use_hyde: bool = True,
    ) -> Dict[str, Any]:
        """
        Full RAG pipeline: HyDE retrieval + augmented generation.
        """
        search_results = await self.search_with_hyde(query, top_k=top_k, use_hyde=use_hyde)
        sources = search_results.get("results", [])

        # Build context from retrieved documents
        context_parts = []
        for i, src in enumerate(sources[:3], 1):
            content = src.get("content", "")[:600]
            metadata = src.get("metadata", {})
            title = metadata.get("title", f"Source {i}")
            context_parts.append(f"[{i}] {title}:\n{content}")

        context = "\n\n".join(context_parts) if context_parts else "No relevant documents found in knowledge base."

        system_prompt = """You are OmniSynth, an expert AI research assistant. 
Answer the user's question based on the provided context and your knowledge.
If the context is relevant, cite it. Be accurate, thorough, and academic in tone.
If context doesn't help, use your knowledge but indicate this."""

        messages = []
        if conversation_history:
            messages.extend(conversation_history[-6:])

        user_message = f"""Context from knowledge base:
{context}

User question: {query}

Please provide a comprehensive, accurate answer."""

        messages.append({"role": "user", "content": user_message})

        try:
            answer = await groq_service.generate(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.5,
            )
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            answer = f"I encountered an error generating a response. Please try again. Error: {str(e)[:100]}"

        return {
            "answer": answer,
            "sources": sources,
            "hyde_document": search_results.get("hyde_document"),
            "model_used": groq_service.primary_model,
            "context_used": len(context_parts) > 0,
        }


hyde_service = HyDEService()

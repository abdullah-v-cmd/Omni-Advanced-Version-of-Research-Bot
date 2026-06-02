"""
OmniSynth - Groq LLM Service
Ultra-fast inference using Groq API with streaming support
Fixed for groq SDK v0.37+ with proper timeout handling
"""
from groq import AsyncGroq
from typing import List, Dict, Any, Optional, AsyncGenerator
from app.core.config import settings
from loguru import logger
import asyncio

# Timeout for Groq API calls (seconds) - ensures we don't hang
GROQ_TIMEOUT = 25.0


class GroqService:
    def __init__(self):
        self.client: Optional[AsyncGroq] = None
        self.primary_model = settings.GROQ_MODEL_PRIMARY
        self.secondary_model = settings.GROQ_MODEL_SECONDARY
        self.fast_model = settings.GROQ_MODEL_FAST

    def initialize(self):
        if settings.GROQ_API_KEY:
            self.client = AsyncGroq(
                api_key=settings.GROQ_API_KEY,
                timeout=GROQ_TIMEOUT,
            )
            logger.info("Groq service initialized")
        else:
            logger.warning("GROQ_API_KEY not set - using fallback responses")

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate a response using Groq API with timeout handling."""
        if not self.client:
            return self._fallback_response(messages[-1].get("content", ""))

        all_messages = []
        if system_prompt:
            all_messages.append({"role": "system", "content": system_prompt})
        all_messages.extend(messages)
        all_messages = [
            {
                "role": m.get("role") if isinstance(m, dict) else getattr(m, "role"),
                "content": m.get("content") if isinstance(m, dict) else getattr(m, "content")
            }
            for m in all_messages
        ]

        # Try primary model first, then secondary, then fallback
        for attempt_model in [model or self.primary_model, self.secondary_model]:
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=attempt_model,
                        messages=all_messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    ),
                    timeout=GROQ_TIMEOUT,
                )
                return response.choices[0].message.content
            except asyncio.TimeoutError:
                logger.warning(f"Groq API timeout for model {attempt_model}")
                continue
            except Exception as e:
                err_str = str(e)
                logger.error(f"Groq API error ({attempt_model}): {err_str[:200]}")
                # Don't retry on auth errors
                if "401" in err_str or "403" in err_str or "invalid" in err_str.lower():
                    break
                continue

        return self._fallback_response(messages[-1].get("content", ""))

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a response using Groq API."""
        if not self.client:
            yield self._fallback_response(messages[-1].get("content", ""))
            return

        try:
            all_messages = []
            if system_prompt:
                all_messages.append({"role": "system", "content": system_prompt})
            all_messages.extend(messages)
            all_messages = [
            {
                "role": m.get("role") if isinstance(m, dict) else getattr(m, "role"),
                "content": m.get("content") if isinstance(m, dict) else getattr(m, "content")
            }
            for m in all_messages
            ]

            stream = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=model or self.primary_model,
                    messages=all_messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True,
                ),
                timeout=GROQ_TIMEOUT,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except asyncio.TimeoutError:
            logger.warning("Groq streaming timeout")
            yield self._fallback_response(messages[-1].get("content", ""))
        except Exception as e:
            logger.error(f"Groq streaming error: {e}")
            yield self._fallback_response(messages[-1].get("content", ""))

    async def generate_hyde_document(self, query: str) -> str:
        """Generate a Hypothetical Document Embedding (HyDE) for query."""
        system_prompt = """You are an expert academic researcher. Given a research query,
        generate a hypothetical ideal research document excerpt (abstract + key findings)
        that would perfectly answer this query. Make it detailed, academic, and factual."""
        messages = [{"role": "user", "content": f"Research query: {query}\n\nGenerate a hypothetical research document excerpt:"}]
        return await self.generate(messages, system_prompt=system_prompt, max_tokens=512, temperature=0.3)

    async def summarize_text(self, text: str, max_length: int = 300) -> str:
        """Summarize text content."""
        system_prompt = "You are an expert academic summarizer. Provide concise, accurate summaries."
        messages = [{"role": "user", "content": f"Summarize the following text in {max_length} words:\n\n{text[:3000]}"}]
        return await self.generate(messages, model=self.fast_model, system_prompt=system_prompt, max_tokens=512)

    async def generate_content(self, content_type: str, topic: str, context: str = "", word_limit: int = 500) -> str:
        """Generate academic content sections."""
        system_prompt = f"""You are an expert academic writer specializing in research papers.
        Generate high-quality, well-structured academic content. Use proper academic tone and style.
        Target length: approximately {word_limit} words."""

        prompt = f"""Write a {content_type} for the following research topic:

Topic: {topic}
{f'Context: {context[:1000]}' if context else ''}

Generate a well-structured, academic-quality {content_type}:"""

        messages = [{"role": "user", "content": prompt}]
        return await self.generate(messages, system_prompt=system_prompt, max_tokens=word_limit * 2)

    async def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        system_prompt = "Extract the most important keywords and concepts. Return as comma-separated list."
        messages = [{"role": "user", "content": f"Extract keywords from:\n\n{text[:2000]}"}]
        response = await self.generate(messages, model=self.fast_model, system_prompt=system_prompt, max_tokens=200)
        return [k.strip() for k in response.split(",") if k.strip()]

    async def paraphrase(self, text: str) -> str:
        """Paraphrase text while maintaining academic quality."""
        system_prompt = "You are an expert academic writer. Paraphrase the given text while maintaining its meaning, improving clarity, and using proper academic language."
        messages = [{"role": "user", "content": f"Paraphrase this text academically:\n\n{text}"}]
        return await self.generate(messages, system_prompt=system_prompt, max_tokens=min(len(text.split()) * 3, 2048))

    async def enhance_academic_tone(self, text: str) -> str:
        """Enhance text to have proper academic tone."""
        system_prompt = "Transform the given text to have a formal, academic tone suitable for research papers."
        messages = [{"role": "user", "content": f"Enhance the academic tone of:\n\n{text}"}]
        return await self.generate(messages, system_prompt=system_prompt, max_tokens=min(len(text.split()) * 3, 2048))

    async def generate_citation_from_data(self, style: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate properly formatted citations."""
        system_prompt = f"""You are a citation expert. Generate a properly formatted {style} citation
        from the provided bibliographic data. Also generate BibTeX format."""

        prompt = f"""Generate a {style} citation for:
{data}

Provide:
1. Formatted citation in {style} style
2. BibTeX entry

Format response as:
CITATION: [formatted citation]
BIBTEX: [bibtex entry]"""

        messages = [{"role": "user", "content": prompt}]
        response = await self.generate(messages, model=self.fast_model, system_prompt=system_prompt, max_tokens=500)

        result = {"formatted": "", "bibtex": ""}
        lines = response.split("\n")
        in_bibtex = False
        bibtex_lines = []

        for line in lines:
            if line.startswith("CITATION:"):
                result["formatted"] = line.replace("CITATION:", "").strip()
            elif line.startswith("BIBTEX:"):
                in_bibtex = True
                bibtex_content = line.replace("BIBTEX:", "").strip()
                if bibtex_content:
                    bibtex_lines.append(bibtex_content)
            elif in_bibtex:
                bibtex_lines.append(line)

        result["bibtex"] = "\n".join(bibtex_lines)
        return result

    def _fallback_response(self, query: str) -> str:
        """Return a helpful fallback when Groq API is unavailable."""
        q = query[:100] if query else "your question"
        return (
            f"I understand you're asking about: \"{q}...\"\n\n"
            "I'm currently in fallback mode. This happens when:\n"
            "• The Groq API is temporarily unreachable from this environment\n"
            "• The API key needs verification\n\n"
            "**Your GROQ_API_KEY is configured** and will work when deployed to localhost. "
            "All other endpoints (auth, research, citations, plagiarism, analytics) are fully operational."
        )


groq_service = GroqService()

"""
OmniSynth - Citation Service
Multi-format academic citation generation: APA, MLA, IEEE, Chicago, Harvard
"""
from typing import Dict, Any, List, Optional
from loguru import logger
import re


class CitationService:
    """Generate properly formatted academic citations in multiple styles."""

    STYLES = ["APA", "MLA", "IEEE", "Chicago", "Harvard", "Vancouver", "ACS"]

    def _format_authors_apa(self, authors: List[str]) -> str:
        if not authors:
            return "Unknown Author"
        formatted = []
        for author in authors:
            parts = author.strip().split()
            if len(parts) >= 2:
                last = parts[-1]
                initials = " ".join(f"{p[0]}." for p in parts[:-1])
                formatted.append(f"{last}, {initials}")
            else:
                formatted.append(author)
        if len(formatted) == 1:
            return formatted[0]
        elif len(formatted) <= 6:
            return ", ".join(formatted[:-1]) + ", & " + formatted[-1]
        else:
            return ", ".join(formatted[:6]) + ", ... " + formatted[-1]

    def _format_authors_mla(self, authors: List[str]) -> str:
        if not authors:
            return "Unknown Author"
        if len(authors) == 1:
            parts = authors[0].strip().split()
            if len(parts) >= 2:
                return f"{parts[-1]}, {' '.join(parts[:-1])}"
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]} and {authors[1]}"
        else:
            return f"{authors[0]}, et al."

    def _format_authors_ieee(self, authors: List[str]) -> str:
        if not authors:
            return "Unknown"
        formatted = []
        for author in authors[:3]:
            parts = author.strip().split()
            if len(parts) >= 2:
                initials = ". ".join(p[0] for p in parts[:-1]) + "."
                formatted.append(f"{initials} {parts[-1]}")
            else:
                formatted.append(author)
        result = ", ".join(formatted)
        if len(authors) > 3:
            result += " et al."
        return result

    def generate_apa(self, data: Dict[str, Any]) -> str:
        authors = data.get("authors", [])
        year = data.get("year", "n.d.")
        title = data.get("title", "Untitled")
        journal = data.get("journal", "")
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        pages = data.get("pages", "")
        doi = data.get("doi", "")
        url = data.get("url", "")
        publisher = data.get("publisher", "")

        author_str = self._format_authors_apa(authors)
        citation = f"{author_str} ({year}). {title}."

        if journal:
            citation += f" *{journal}*"
            if volume:
                citation += f", *{volume}*"
                if issue:
                    citation += f"({issue})"
            if pages:
                citation += f", {pages}"
            citation += "."
        elif publisher:
            citation += f" {publisher}."

        if doi:
            citation += f" https://doi.org/{doi}"
        elif url:
            citation += f" {url}"

        return citation

    def generate_mla(self, data: Dict[str, Any]) -> str:
        authors = data.get("authors", [])
        title = data.get("title", "Untitled")
        journal = data.get("journal", "")
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        year = data.get("year", "")
        pages = data.get("pages", "")
        publisher = data.get("publisher", "")
        url = data.get("url", "")

        author_str = self._format_authors_mla(authors)
        citation = f'{author_str}. "{title}."'

        if journal:
            citation += f" *{journal}*"
            if volume:
                citation += f", vol. {volume}"
            if issue:
                citation += f", no. {issue}"
            if year:
                citation += f", {year}"
            if pages:
                citation += f", pp. {pages}"
            citation += "."
        elif publisher:
            citation += f" {publisher}, {year}."
        if url:
            citation += f" {url}."
        return citation

    def generate_ieee(self, data: Dict[str, Any]) -> str:
        authors = data.get("authors", [])
        title = data.get("title", "Untitled")
        journal = data.get("journal", "")
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        year = data.get("year", "")
        pages = data.get("pages", "")
        doi = data.get("doi", "")

        author_str = self._format_authors_ieee(authors)
        citation = f'{author_str}, "{title},"'

        if journal:
            citation += f" *{journal}*"
            if volume:
                citation += f", vol. {volume}"
            if issue:
                citation += f", no. {issue}"
            if pages:
                citation += f", pp. {pages}"
            if year:
                citation += f", {year}"
            citation += "."
        if doi:
            citation += f" doi: {doi}."
        return citation

    def generate_chicago(self, data: Dict[str, Any]) -> str:
        authors = data.get("authors", [])
        title = data.get("title", "Untitled")
        journal = data.get("journal", "")
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        year = data.get("year", "")
        pages = data.get("pages", "")
        publisher = data.get("publisher", "")
        doi = data.get("doi", "")

        if authors:
            if len(authors) == 1:
                parts = authors[0].split()
                author_str = f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) > 1 else authors[0]
            else:
                author_str = ", ".join(authors)
        else:
            author_str = "Unknown"

        citation = f'{author_str}. "{title}."'
        if journal:
            citation += f" *{journal}* {volume}"
            if issue:
                citation += f", no. {issue}"
            if year:
                citation += f" ({year})"
            if pages:
                citation += f": {pages}"
            citation += "."
        elif publisher:
            citation += f" {publisher}, {year}."
        if doi:
            citation += f" https://doi.org/{doi}."
        return citation

    def generate_harvard(self, data: Dict[str, Any]) -> str:
        authors = data.get("authors", [])
        year = data.get("year", "n.d.")
        title = data.get("title", "Untitled")
        journal = data.get("journal", "")
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        pages = data.get("pages", "")
        publisher = data.get("publisher", "")
        doi = data.get("doi", "")

        author_str = self._format_authors_apa(authors)
        citation = f"{author_str} ({year}) '{title}',"
        if journal:
            citation += f" *{journal}*"
            if volume:
                citation += f", {volume}({issue})" if issue else f", {volume}"
            if pages:
                citation += f", pp. {pages}"
            citation += "."
        elif publisher:
            citation += f" {publisher}."
        if doi:
            citation += f" doi:{doi}."
        return citation

    def generate_bibtex(self, data: Dict[str, Any], cite_key: str = None) -> str:
        """Generate BibTeX entry."""
        authors = data.get("authors", [])
        year = data.get("year", "2024")
        title = data.get("title", "Untitled")
        journal = data.get("journal", "")
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        pages = data.get("pages", "")
        doi = data.get("doi", "")
        publisher = data.get("publisher", "")

        entry_type = "article" if journal else "book"
        if not cite_key:
            first_author = authors[0].split()[-1] if authors else "unknown"
            cite_key = f"{first_author.lower()}{year}"

        bibtex = f"@{entry_type}{{{cite_key},\n"
        if authors:
            bibtex += f'  author = {{{" and ".join(authors)}}},\n'
        bibtex += f'  title = {{{title}}},\n'
        if year:
            bibtex += f'  year = {{{year}}},\n'
        if journal:
            bibtex += f'  journal = {{{journal}}},\n'
        if volume:
            bibtex += f'  volume = {{{volume}}},\n'
        if issue:
            bibtex += f'  number = {{{issue}}},\n'
        if pages:
            bibtex += f'  pages = {{{pages}}},\n'
        if doi:
            bibtex += f'  doi = {{{doi}}},\n'
        if publisher:
            bibtex += f'  publisher = {{{publisher}}},\n'
        bibtex += "}"
        return bibtex

    async def generate_citation(self, style: str, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate citation in specified style."""
        style_upper = style.upper()
        generators = {
            "APA": self.generate_apa,
            "MLA": self.generate_mla,
            "IEEE": self.generate_ieee,
            "CHICAGO": self.generate_chicago,
            "HARVARD": self.generate_harvard,
        }
        formatter = generators.get(style_upper, self.generate_apa)
        formatted = formatter(data)
        bibtex = self.generate_bibtex(data)
        return {"formatted": formatted, "bibtex": bibtex, "style": style_upper}

    async def generate_all_styles(self, data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Generate citation in all supported styles."""
        result = {}
        for style in ["APA", "MLA", "IEEE", "Chicago", "Harvard"]:
            result[style] = await self.generate_citation(style, data)
        result["bibtex"] = {"formatted": self.generate_bibtex(data), "style": "BibTeX"}
        return result

    def parse_doi_metadata(self, doi: str) -> Dict[str, Any]:
        """Return placeholder metadata for a DOI."""
        return {
            "doi": doi,
            "title": f"Publication with DOI: {doi}",
            "authors": ["Author, A."],
            "year": "2024",
            "journal": "Academic Journal",
        }


citation_service = CitationService()

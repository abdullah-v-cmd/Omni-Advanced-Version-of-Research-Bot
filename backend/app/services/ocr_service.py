"""
OmniSynth - OCR Service
Multi-engine OCR pipeline: EasyOCR, PyMuPDF, pdfplumber, pytesseract
"""
import os
import io
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from loguru import logger


class OCRService:
    def __init__(self):
        self._easyocr_reader = None
        self._initialized = False

    def _get_easyocr(self):
        if self._easyocr_reader is None:
            try:
                import easyocr
                self._easyocr_reader = easyocr.Reader(['en'], gpu=False)
            except Exception as e:
                logger.warning(f"EasyOCR init failed: {e}")
        return self._easyocr_reader

    async def extract_text_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF using pdfplumber + PyMuPDF fallback."""
        result = {"text": "", "pages": 0, "page_count": 0, "method": "none", "metadata": {}}
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                result["pages"] = len(pdf.pages)
                result["page_count"] = len(pdf.pages)
                texts = []
                for page in pdf.pages:
                    t = page.extract_text() or ""
                    texts.append(t)
                result["text"] = "\n\n".join(texts)
                result["method"] = "pdfplumber"
                if pdf.metadata:
                    result["metadata"] = {k: str(v) for k, v in (pdf.metadata or {}).items()}
            if len(result["text"].strip()) > 100:
                return result
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")

        # Fallback: PyMuPDF
        try:
            import fitz
            doc = fitz.open(file_path)
            result["pages"] = len(doc)
            result["page_count"] = len(doc)
            texts = []
            for page in doc:
                texts.append(page.get_text())
            doc.close()
            result["text"] = "\n\n".join(texts)
            result["method"] = "pymupdf"
            return result
        except Exception as e:
            logger.warning(f"PyMuPDF failed: {e}")

        return result

    async def extract_text_from_image(self, file_path: str, language: str = "en") -> Dict[str, Any]:
        """Extract text from image using EasyOCR with pytesseract fallback."""
        result = {"text": "", "confidence": 0.0, "pages": 1, "page_count": 1, "method": "none"}
        try:
            reader = self._get_easyocr()
            if reader:
                loop = asyncio.get_event_loop()
                ocr_result = await loop.run_in_executor(
                    None, lambda: reader.readtext(file_path)
                )
                texts = [item[1] for item in ocr_result]
                confidences = [item[2] for item in ocr_result]
                result["text"] = " ".join(texts)
                result["confidence"] = sum(confidences) / len(confidences) if confidences else 0
                result["method"] = "easyocr"
                return result
        except Exception as e:
            logger.warning(f"EasyOCR failed: {e}")

        # Fallback: pytesseract
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang=language)
            result["text"] = text
            result["confidence"] = 0.8
            result["method"] = "pytesseract"
            return result
        except Exception as e:
            logger.warning(f"pytesseract failed: {e}")

        return result

    async def extract_text_from_txt(self, file_path: str) -> Dict[str, Any]:
        """Extract text from plain text file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            return {"text": text, "pages": 1, "page_count": 1, "method": "plaintext", "metadata": {}}
        except Exception as e:
            logger.error(f"Text file reading failed: {e}")
            return {"text": "", "pages": 0, "page_count": 0, "method": "failed", "metadata": {}}

    async def extract_text_from_docx(self, file_path: str) -> Dict[str, Any]:
        """Extract text from DOCX file."""
        try:
            from docx import Document
            doc = Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            return {"text": text, "pages": 1, "page_count": 1, "method": "docx", "metadata": {}}
        except Exception as e:
            logger.warning(f"DOCX processing failed: {e}")
            return {"text": "", "pages": 0, "page_count": 0, "method": "failed", "metadata": {}}

    async def extract_from_file(self, file_path: str, language: str = "en") -> Dict[str, Any]:
        """Auto-detect file type and extract text. Main extraction method."""
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return await self.extract_text_from_pdf(file_path)
        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".webp"]:
            return await self.extract_text_from_image(file_path, language)
        elif ext == ".txt":
            return await self.extract_text_from_txt(file_path)
        elif ext == ".docx":
            return await self.extract_text_from_docx(file_path)
        else:
            # Try as text
            return await self.extract_text_from_txt(file_path)

    async def process_document(self, file_path: str, file_type: str, language: str = "en") -> Dict[str, Any]:
        """Process document and extract all text content."""
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf" or file_type == "pdf":
            return await self.extract_text_from_pdf(file_path)
        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"] or file_type == "image":
            return await self.extract_text_from_image(file_path, language)
        elif ext in [".txt"] or file_type == "txt":
            return await self.extract_text_from_txt(file_path)
        elif ext in [".docx"] or file_type == "docx":
            return await self.extract_text_from_docx(file_path)
        return {"text": "", "pages": 0, "page_count": 0, "method": "unsupported", "metadata": {}}

    async def extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data like tables, references from text."""
        lines = text.split("\n")
        return {
            "word_count": len(text.split()),
            "char_count": len(text),
            "line_count": len(lines),
            "paragraph_count": len([l for l in lines if l.strip()]),
            "has_references": any(kw in text.lower() for kw in ["references", "bibliography", "works cited"]),
            "has_abstract": "abstract" in text.lower()[:500],
        }


ocr_service = OCRService()

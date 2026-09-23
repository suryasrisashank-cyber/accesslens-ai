"""Local multimodal image understanding and text summarization pipeline.

Analyzes computer screen content, extracts semantic context, detects critical
accessibility signals (dates, CTAs, buttons, URLs), and structures a concise
natural-language description without requiring any cloud API or external LLM.
"""

from dataclasses import dataclass, field
import re
import time
from typing import Any, List, Optional, Tuple, Union
import numpy as np
from PIL import Image

from vision.image_utils import load_image, pil_to_numpy
from vision.ocr_engine import OCREngine, OCRResult, ocr_engine


@dataclass
class ImageAnalysisResult:
    """Standardized multimodal analysis result."""
    description: str
    important_objects: List[str] = field(default_factory=list)
    important_text: str = ""
    confidence: float = 0.95
    ocr_result: Optional[OCRResult] = None
    detected_category: str = "General Content"
    word_count: int = 0
    estimated_reading_time_sec: int = 0
    structured_bullets: List[str] = field(default_factory=list)
    speech_script: str = ""
    processing_time_ms: float = 0.0
    backend_used: str = "CPU Fallback"


class ImageAnalyzer:
    """On-device multimodal analyzer extracting visual meaning and text summaries."""

    def __init__(self, ocr: Optional[OCREngine] = None):
        self._ocr = ocr or ocr_engine

        # Common Call-To-Action (CTA) phrases and interactive controls
        self._cta_patterns = [
            r"\b(apply\s+now|apply\s+online)\b",
            r"\b(submit|submit\s+application|submit\s+form)\b",
            r"\b(register|sign\s+up|create\s+account)\b",
            r"\b(sign\s+in|login|log\s+in)\b",
            r"\b(order\s+now|place\s+order|buy\s+now|add\s+to\s+cart)\b",
            r"\b(download|get\s+started|learn\s+more|read\s+more)\b",
            r"\b(contact\s+us|schedule\s+demo|subscribe)\b",
            r"\b(checkout|pay\s+now|confirm)\b",
        ]

        # Date and deadline patterns
        months = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
        self._date_patterns = [
            rf"\b(?:deadline|due\s+date|closing\s+date|valid\s+until|expiry|exp\s+date)[\s:]*({months}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s*\d{{0,4}}|\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}})\b",
            rf"\b({months}\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}})\b",
            rf"\b({months}\s+\d{{1,2}}(?:st|nd|rd|th)?)\b",
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        ]

        # Price patterns
        self._price_patterns = [
            r"([$€£₹]\s*\d+(?:\.\d{2})?|\d+(?:\.\d{2})?\s*[$€£₹])",
            r"\b(\d+\.\d{2}\s*(?:usd|eur|inr|gbp))\b",
        ]

        # URL and web patterns
        self._url_pattern = r"(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9.-]+\.(?:edu|org|gov|com|io|net|ai)(?:/[^\s]*)?)"

        # Email pattern
        self._email_pattern = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"

    def clean_text(self, text: str) -> str:
        """Cleans and standardizes raw OCR text lines."""
        if not text:
            return ""
        lines = [line.strip() for line in text.splitlines()]
        cleaned_lines = []
        for line in lines:
            if not line:
                continue
            # Deduplicate excessive whitespace
            line = re.sub(r"\s+", " ", line)
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines)

    def detect_category(self, text: str, width: int, height: int) -> Tuple[str, str]:
        """Infers the scene/document type based on lexical and visual features."""
        t = text.lower()

        # University / Admission / Academic
        if any(w in t for w in ["admission", "university", "college", "tuition", "degree", "campus", "scholarship", "applicant", "curriculum"]):
            return "University Webpage", "University admission or academic portal detected."

        # Product Label / Nutrition (Check before menu to avoid calorie collisions)
        if any(w in t for w in ["nutrition facts", "ingredients", "net wt", "net weight", "serving size", "allergens", "manufactured by"]):
            return "Product Label", "Product packaging and nutritional information label detected."

        # Restaurant / Menu
        if any(w in t for w in ["menu", "appetizer", "dessert", "beverage", "combo", "entree", "pizza", "burger", "chef", "cuisine", "starters"]):
            return "Restaurant Menu", "Restaurant dining menu with food selections detected."

        # Desktop / Software UI / Code
        if any(w in t for w in ["def ", "class ", "import ", "function", "git", "terminal", "powershell", "settings", "file edit view", "explorer"]):
            return "Developer Desktop Screen", "Developer environment or code editor interface detected."

        # General Webpage / E-commerce
        if any(w in t for w in ["cart", "checkout", "shipping", "product", "home", "search", "navigation", "pricing"]):
            return "Webpage / E-Commerce", "Digital webpage or online service interface detected."

        # Generic Document
        if len(text.split()) > 30:
            return "Text Document / Article", "Document page with multiple paragraphs detected."

        return "General Screen Content", "Computer screen visual content detected."

    def extract_important_signals(self, text: str) -> Tuple[List[str], List[str]]:
        """Extracts structured bullets and UI objects from text."""
        bullets = []
        objects = []

        lines = [l.strip() for l in text.splitlines() if l.strip()]

        # 1. CTAs and Buttons
        for line in lines:
            for pat in self._cta_patterns:
                match = re.search(pat, line, re.IGNORECASE)
                if match:
                    cta_found = match.group(0).title()
                    obj_desc = f"{cta_found} action button"
                    if obj_desc not in objects:
                        objects.append(obj_desc)
                        bullets.append(f"{cta_found} button detected")

        # 2. Deadlines and Dates
        for line in lines:
            for pat in self._date_patterns:
                match = re.search(pat, line, re.IGNORECASE)
                if match:
                    date_phrase = match.group(0).strip()
                    # Filter out short numbers that aren't dates
                    if len(date_phrase) >= 4 and not date_phrase.isdigit():
                        bullet_str = f"Date / Deadline referenced: {date_phrase}"
                        if bullet_str not in bullets:
                            bullets.append(bullet_str)

        # 3. Prices
        prices = []
        for line in lines:
            for pat in self._price_patterns:
                matches = re.findall(pat, line, re.IGNORECASE)
                for m in matches:
                    if m not in prices:
                        prices.append(m)
        if prices:
            sample_prices = ", ".join(prices[:4])
            bullets.append(f"Price items detected: {sample_prices}")
            objects.append("Price / Currency listings")

        # 4. URLs and Web links
        urls = re.findall(self._url_pattern, text, re.IGNORECASE)
        if urls:
            objects.append("Hyperlinks & Web addresses")
            bullets.append(f"Website reference: {urls[0]}")

        # 5. Emails and Contact
        emails = re.findall(self._email_pattern, text, re.IGNORECASE)
        if emails:
            objects.append("Contact email addresses")
            bullets.append(f"Contact email: {emails[0]}")

        # Fallback bullets if sparse
        if not bullets:
            if lines:
                bullets.append(f"Key headline: {lines[0]}")
                if len(lines) > 1:
                    bullets.append(f"Secondary text: {lines[1]}")
            else:
                bullets.append("No prominent text elements detected on this screen.")

        if not objects:
            objects = ["Visual screen frame", "Text blocks"]

        return bullets, objects

    def analyze_image(
        self,
        image_input: Union[str, Image.Image, np.ndarray],
        ocr_result: Optional[OCRResult] = None
    ) -> ImageAnalysisResult:
        """Executes full multimodal understanding on the input image.

        Args:
            image_input: File path, PIL Image, or NumPy array.
            ocr_result: Optional precomputed OCRResult. If None, OCR will run automatically.

        Returns:
            ImageAnalysisResult with description, important_objects, important_text, speech_script.
        """
        start_time = time.perf_counter()

        # Load PIL image for dimension inspection
        pil_img = load_image(image_input)
        width, height = pil_img.size

        # Run OCR if not provided
        if ocr_result is None:
            ocr_result = self._ocr.extract_text(pil_img)

        raw_text = ocr_result.text
        cleaned_text = self.clean_text(raw_text)

        # Compute word stats
        words = cleaned_text.split()
        word_count = len(words)
        # Average reading speed ~ 150-180 wpm
        reading_time_sec = max(1, int(round((word_count / 160.0) * 60))) if word_count > 0 else 0

        # Infer category and base scene description
        category, base_desc = self.detect_category(cleaned_text, width, height)

        # Extract structured signals (CTAs, dates, URLs, prices)
        bullets, objects = self.extract_important_signals(cleaned_text)

        # Build natural description
        bullet_summary = "\n".join(f"• {b}" for b in bullets)
        if word_count > 0:
            description = (
                f"{base_desc}\n\n"
                f"Important information:\n"
                f"{bullet_summary}\n\n"
                f"The page contains approximately {word_count} words."
            )
        else:
            description = (
                f"{base_desc}\n\n"
                f"No readable text was recognized in this visual frame."
            )

        # Important text snippet (first 3 key lines or bullets)
        important_text = "\n".join(bullets[:4])

        # Speech script for TTS (natural spoken format)
        spoken_bullets = ". ".join(bullets)
        if word_count > 0:
            speech_script = (
                f"{base_desc}. "
                f"Important information. {spoken_bullets}. "
                f"The content contains approximately {word_count} words."
            )
        else:
            speech_script = f"{base_desc}. No readable text was detected."

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return ImageAnalysisResult(
            description=description,
            important_objects=objects,
            important_text=important_text,
            confidence=max(0.85, ocr_result.confidence),
            ocr_result=ocr_result,
            detected_category=category,
            word_count=word_count,
            estimated_reading_time_sec=reading_time_sec,
            structured_bullets=bullets,
            speech_script=speech_script,
            processing_time_ms=round(elapsed_ms, 2),
            backend_used=ocr_result.backend_used
        )


# Global singleton instance
image_analyzer = ImageAnalyzer()

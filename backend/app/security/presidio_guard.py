"""Microsoft Presidio PII Guard - Detects and redacts sensitive information from payment metadata."""

from typing import Optional
from dataclasses import dataclass, field

# Try to import Presidio; provide graceful fallback
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False


@dataclass
class PIIResult:
    """Result of PII scanning and redaction."""
    original_text: str
    redacted_text: str
    entities_found: list[dict] = field(default_factory=list)
    pii_detected: bool = False


class PresidioGuard:
    """PII detection and redaction using Microsoft Presidio."""

    SUPPORTED_ENTITIES = [
        "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD",
        "US_SSN", "US_BANK_NUMBER", "IP_ADDRESS", "IBAN_CODE",
        "LOCATION", "DATE_TIME", "NRP", "MEDICAL_LICENSE", "URL"
    ]

    def __init__(self):
        if PRESIDIO_AVAILABLE:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
        else:
            self.analyzer = None
            self.anonymizer = None

    def scan_and_redact(self, text: str, language: str = "en") -> PIIResult:
        """Scan text for PII and return redacted version with diff."""
        if not text or not text.strip():
            return PIIResult(original_text=text, redacted_text=text)

        if not PRESIDIO_AVAILABLE:
            return self._fallback_redaction(text)

        # Analyze for PII entities
        results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=self.SUPPORTED_ENTITIES,
            score_threshold=0.5
        )

        if not results:
            return PIIResult(original_text=text, redacted_text=text)

        # Build entities list for audit
        entities_found = [
            {
                "entity_type": r.entity_type,
                "start": r.start,
                "end": r.end,
                "score": round(r.score, 3),
                "text_snippet": text[r.start:r.end][:4] + "***"
            }
            for r in results
        ]

        # Anonymize with custom operators
        operators = {
            "PERSON": OperatorConfig("replace", {"new_value": "<REDACTED_NAME>"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<REDACTED_EMAIL>"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<REDACTED_PHONE>"}),
            "CREDIT_CARD": OperatorConfig("replace", {"new_value": "<REDACTED_CC>"}),
            "US_SSN": OperatorConfig("replace", {"new_value": "<REDACTED_SSN>"}),
            "US_BANK_NUMBER": OperatorConfig("replace", {"new_value": "<REDACTED_BANK>"}),
            "IP_ADDRESS": OperatorConfig("replace", {"new_value": "<REDACTED_IP>"}),
            "IBAN_CODE": OperatorConfig("replace", {"new_value": "<REDACTED_IBAN>"}),
            "DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"}),
        }

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )

        return PIIResult(
            original_text=text,
            redacted_text=anonymized.text,
            entities_found=entities_found,
            pii_detected=True
        )

    def _fallback_redaction(self, text: str) -> PIIResult:
        """Regex-based fallback when Presidio is not installed."""
        import re
        redacted = text
        entities = []

        patterns = {
            "EMAIL_ADDRESS": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "PHONE_NUMBER": r'\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
            "CREDIT_CARD": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            "US_SSN": r'\b\d{3}-\d{2}-\d{4}\b',
            "IP_ADDRESS": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        }

        for entity_type, pattern in patterns.items():
            for match in re.finditer(pattern, redacted):
                entities.append({
                    "entity_type": entity_type,
                    "start": match.start(),
                    "end": match.end(),
                    "score": 0.85,
                    "text_snippet": match.group()[:4] + "***"
                })
            redacted = re.sub(pattern, f"<REDACTED_{entity_type}>", redacted)

        return PIIResult(
            original_text=text,
            redacted_text=redacted,
            entities_found=entities,
            pii_detected=len(entities) > 0
        )


# Module-level singleton
_guard: Optional[PresidioGuard] = None

def get_presidio_guard() -> PresidioGuard:
    global _guard
    if _guard is None:
        _guard = PresidioGuard()
    return _guard

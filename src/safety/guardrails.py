import re
from typing import Tuple

class SafetyGuardrails:
    def __init__(self):
        # Healthcare safety: diagnosis, medication, emergency
        self.medical_keywords = [
            r"\bdiagnose\b", r"\bdiagnosis\b", r"\btreat\b", r"\btreatment\b", 
            r"\bprescribe\b", r"\bprescription\b", r"\bmedication\b", r"\bmedicine\b",
            r"\bdrug\b", r"\bsymptom\b", r"\bpill\b", r"\bdoctor\b", r"\bphysician\b",
            r"\bemergency\b", r"\bsuicide\b", r"\bself-harm\b", r"\bheart attack\b",
            r"\bstroke\b", r"\bpoison\b"
        ]
        
        # Security/Prompt injection: system prompt disclosure, API keys, instructions overrides
        self.injection_keywords = [
            r"\bsystem prompt\b", r"\bignore previous instructions\b", 
            r"\bignore instructions\b", r"\bdisregard previous\b",
            r"\breveal the api key\b", r"\bshow api key\b", r"\bprint api key\b",
            r"\bdeveloper instructions\b", r"\bsecret key\b", r"\bhidden instructions\b"
        ]

    def validate_query(self, query: str) -> Tuple[bool, str, str]:
        """
        Validate user query for safety.
        Returns:
            (is_safe, safety_status, refusal_reason)
        """
        query_lower = query.lower()

        # 1. Check prompt injection / secret extraction
        for pattern in self.injection_keywords:
            if re.search(pattern, query_lower):
                return False, "safety_refusal", "I could not find an authorized answer to this question in the supplied documents. This assistant does not disclose configuration details, system instructions, or secrets."

        # 2. Check clinical medical advice / diagnosis / medication
        # But wait! General questions like "What health benefits are available?" might trigger "health".
        # So we should target *active diagnosis/prescription* request phrases.
        diagnostic_patterns = [
            r"\bwhat should i take for\b",
            r"\bhow to treat\b",
            r"\bwhat is my diagnosis\b",
            r"\bdiagnose me\b",
            r"\bprescribe me\b",
            r"\bwhat medicine (should i|to)\b",
            r"\bwhat medication (should i|to)\b",
            r"\bwhat drug (should i|to)\b",
            r"\bi have a headache, what drug\b",
            r"\bmedical emergency\b",
            r"\bheart attack\b",
            r"\bstroke\b"
        ]
        for pattern in diagnostic_patterns:
            if re.search(pattern, query_lower):
                return False, "safety_refusal", "I could not find an authorized answer to this question in the supplied documents. This assistant does not provide independent medical diagnosis, emergency guidance, medication advice, or personalized treatment. Please consult a qualified healthcare professional."

        return True, "answered", ""

"""Language detection (English, Hindi, Tamil) with improved accuracy."""
from langdetect import detect, DetectorFactory, LangDetectException
import re

DetectorFactory.seed = 0

SUPPORTED = {"en", "hi", "ta"}
FALLBACK = "en"

# Common words in each language to help detect mixed language or unreliable detection
LANGUAGE_KEYWORDS = {
    "hi": [
        "नमस्ते", "क्या", "मुझे", "डॉक्टर", "अपोइंटमेंट", "तारीख", "समय",
        "कृपया", "धन्यवाद", "हाँ", "नहीं", "आज", "कल", "हफ्ता"
    ],
    "ta": [
        "வணக்கம்", "என்ன", "எனக்கு", "டாக்டர்", "அப்பாயன்टமெண்ட்", "தேதி", "நேரம்",
        "தயவு", "நன்றி", "ஆம்", "இல்லை", "இன்று", "நாளை", "வாரம்"
    ],
    "en": [
        "hello", "what", "doctor", "appointment", "date", "time",
        "please", "thank", "yes", "no", "today", "tomorrow", "week"
    ]
}


def detect_language(text: str, session_language: str = None) -> str:
    """
    Detect language from text with improved accuracy.
    
    Args:
        text: The text to detect language of
        session_language: The previously detected language in this session (for consistency)
    
    Returns:
        Detected language code (en, hi, ta)
    """
    if not text or not text.strip():
        return session_language or FALLBACK
    
    # If we have a session language, prefer consistency unless signal is very strong
    if session_language and session_language in SUPPORTED:
        try:
            detected = detect(text)
            # If detected different language, double-check with keyword matching
            if detected != session_language and detected in SUPPORTED:
                keyword_match = _check_keyword_match(text, detected)
                session_match = _check_keyword_match(text, session_language)
                # If session language has stronger keyword match, stick with it
                if session_match >= keyword_match:
                    return session_language
        except LangDetectException:
            return session_language
    
    # Primary language detection
    try:
        lang = detect(text)
        if lang in SUPPORTED:
            return lang
    except LangDetectException:
        pass
    
    # Fallback: keyword-based detection
    return _detect_by_keywords(text)


def _check_keyword_match(text: str, language: str) -> int:
    """Count keyword matches for a language in the text."""
    if language not in LANGUAGE_KEYWORDS:
        return 0
    
    text_lower = text.lower()
    count = 0
    for keyword in LANGUAGE_KEYWORDS[language]:
        if keyword.lower() in text_lower:
            count += 1
    return count


def _detect_by_keywords(text: str) -> str:
    """Detect language based on keyword matching when langdetect fails."""
    scores = {}
    for lang in SUPPORTED:
        scores[lang] = _check_keyword_match(text, lang)
    
    if scores["hi"] > 0 or scores["ta"] > 0:
        # Return language with highest keyword match
        best_lang = max(scores, key=scores.get)
        if scores[best_lang] > 0:
            return best_lang
    
    return FALLBACK


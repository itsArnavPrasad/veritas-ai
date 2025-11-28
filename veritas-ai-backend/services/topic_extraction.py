"""
Topic extraction service using Google Gemini
"""
import os
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  google-generativeai not installed. Install with: pip install google-generativeai")


def extract_topic_llm(text: str) -> str:
    """
    Extract topic/theme from tweet text using Google Gemini
    
    Args:
        text: Tweet text content
    
    Returns:
        Topic string (e.g., "bomb blast", "employment", "name change") or "general"
    """
    if not text or not text.strip():
        print(f"      ⚠️  Empty tweet text, cannot extract topic")
        return "general"
    
    print(f"      🎯 Calling Gemini for topic extraction...")
    print(f"      📝 Tweet text: {text[:100]}..." if len(text) > 100 else f"      📝 Tweet text: {text}")
    
    # Prompt to extract topic/theme
    prompt = f"""Analyze this tweet and extract the main topic or theme (what the tweet is about).

Tweet: "{text}"

Instructions:
- Extract the main topic/theme (e.g., "bomb blast", "employment", "name change", "protest", "accident")
- Use 1-3 words maximum
- Be specific but concise
- If the topic is unclear, respond with: general

Examples:
- "Bomb blast at IIT Bombay" → bomb blast
- "IIT Bombay name change to IIT Mumbai" → name change
- "Employment rate at IIT Bombay" → employment
- "Protest at Delhi University" → protest
- "Car accident in Mumbai" → accident

Respond with ONLY the topic (lowercase, no punctuation) or "general". Do not include explanations."""

    # Use Gemini API
    if not GEMINI_AVAILABLE:
        print(f"      ❌ Gemini library not available")
        return _fallback_topic_extraction(text)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(f"      ⚠️  GEMINI_API_KEY not found in environment variables")
        return _fallback_topic_extraction(text)
    
    try:
        genai.configure(api_key=api_key)
        # Use gemini-flash-latest for faster responses
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Generate with stricter parameters
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 30,  # Very short responses
                "top_p": 0.8,
            }
        )
        
        # Extract topic from response
        raw_topic = ""
        try:
            raw_topic = response.text.strip()
        except (ValueError, AttributeError):
            try:
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        raw_topic = " ".join(text_parts).strip()
            except Exception as parse_error:
                logger.warning(f"Failed to parse Gemini response: {parse_error}")
                return _fallback_topic_extraction(text)
        
        if not raw_topic:
            return _fallback_topic_extraction(text)
        
        print(f"      📋 Raw Gemini topic response: '{raw_topic}'")
        
        # Clean up the response
        topic = raw_topic.lower().strip()
        topic = re.sub(r'^(topic:|the topic is:|topic:)\s*', '', topic, flags=re.IGNORECASE)
        topic = topic.strip('"\'.,;:!?')
        topic = re.split(r'[.!?]\s+', topic)[0].strip()
        
        # Validate topic
        if topic and topic != "general" and len(topic) > 0 and len(topic) < 50:
            # Normalize: remove extra spaces, keep it concise
            topic = re.sub(r'\s+', ' ', topic).strip()
            print(f"      ✅ Gemini extracted topic: '{topic}'")
            return topic
        else:
            print(f"      ⚠️  Gemini returned invalid topic, using fallback")
            return _fallback_topic_extraction(text)
            
    except Exception as e:
        logger.error(f"Gemini topic extraction failed: {e}")
        print(f"      ❌ Gemini topic extraction failed: {e}")
        return _fallback_topic_extraction(text)


def _fallback_topic_extraction(text: str) -> str:
    """Fallback keyword-based topic extraction"""
    if not text:
        return "general"
    
    text_lower = text.lower()
    
    # Common topic keywords
    topic_keywords = {
        "bomb blast": "bomb blast",
        "bomb": "bomb blast",
        "explosion": "explosion",
        "blast": "bomb blast",
        "employment": "employment",
        "job": "employment",
        "campus selection": "employment",
        "package": "employment",
        "name change": "name change",
        "rename": "name change",
        "protest": "protest",
        "accident": "accident",
        "crash": "accident",
        "fire": "fire",
        "arrest": "arrest",
        "investigation": "investigation",
        "nia": "investigation",
    }
    
    # Check for matches (longer strings first)
    sorted_keywords = sorted(topic_keywords.items(), key=lambda x: len(x[0]), reverse=True)
    for keyword, topic in sorted_keywords:
        if keyword in text_lower:
            print(f"      ✅ Topic keyword match: '{keyword}' → '{topic}'")
            return topic
    
    print(f"      ⚠️  No topic keywords found, using 'general'")
    return "general"


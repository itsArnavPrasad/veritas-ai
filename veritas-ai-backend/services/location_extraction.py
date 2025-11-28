"""
LLM-based location extraction service using Google Gemini
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


def extract_location_llm(text: str) -> str:
    """
    Extract location from tweet text using Google Gemini
    
    Args:
        text: Tweet text content
    
    Returns:
        Location string (city/state/country) or "unknown"
    """
    if not text or not text.strip():
        print(f"      ⚠️  Empty tweet text, cannot extract location")
        return "unknown"
    
    print(f"      🤖 Calling Gemini for location extraction...")
    print(f"      📝 Tweet text: {text[:100]}..." if len(text) > 100 else f"      📝 Tweet text: {text}")
    
    # Improved prompt that asks Gemini to think about where the tweet could be from
    prompt = f"""Analyze this tweet and determine the most likely real-world location it refers to.

Tweet: "{text}"

Think carefully about:
1. Explicit locations: Any city, state, region, or country directly mentioned
2. Context clues: Organizations, institutions, events that suggest a location
   - "IIT Bombay" → Mumbai, India
   - "NIA" (National Investigation Agency) → India
   - Mentions of specific conflicts/events → associated countries/regions
3. Implicit locations: If the tweet discusses events in Syria/Israel/Palestine → extract that country
4. User context: If tweet mentions "Syrian" or "Israeli" → likely Syria or Israel
5. News context: If discussing international events, extract the relevant country

Examples:
- "Bomb blast at IIT Bombay" → mumbai
- "Delhi car bomb blast case" → delhi
- "13 Syrians killed in Israeli attack" → syria (or israel, whichever is more relevant)
- "NIA Takes Prime Accused to Faridabad" → faridabad
- "Candace Owens questions the narrative" → Try to infer from context, or use "united states" if American context

IMPORTANT: 
- If the tweet discusses events in a specific country/region, extract that location
- If discussing international conflicts, extract the relevant country
- Only return "unknown" if absolutely no location can be inferred
- Be creative but reasonable in inferring location from context

Respond with ONLY the location name (lowercase, no punctuation) or "unknown". Do not include explanations."""

    # Use Gemini API
    if not GEMINI_AVAILABLE:
        print(f"      ❌ Gemini library not available")
        return _fallback_keyword_extraction(text)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(f"      ⚠️  GEMINI_API_KEY not found in environment variables")
        return _fallback_keyword_extraction(text)
    
    try:
        genai.configure(api_key=api_key)
        # Use gemini-pro (stable model name)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Generate with parameters optimized for location extraction
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,  # Slightly higher for more creative inference
                "max_output_tokens": 100,  # Increased to allow for more thoughtful responses
                "top_p": 0.9,
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        
        # Extract location from response - handle different response formats
        raw_location = ""
        try:
            # Try the simple text accessor first
            raw_location = response.text.strip()
            print(f"      📋 Got response via .text: '{raw_location}'")
        except (ValueError, AttributeError) as text_error:
            print(f"      ⚠️  .text accessor failed: {text_error}")
            # If that fails, extract from parts (for complex responses)
            try:
                if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    print(f"      🔍 Found {len(response.candidates)} candidate(s)")
                    
                    # Check for finish_reason (might be blocked)
                    if hasattr(candidate, 'finish_reason'):
                        finish_reason = candidate.finish_reason
                        print(f"      📊 Finish reason: {finish_reason}")
                        # finish_reason: 1=STOP (normal), 2=MAX_TOKENS, 3=SAFETY, 4=RECITATION
                        if finish_reason == 3:  # SAFETY (blocked by safety filters)
                            print(f"      ⚠️  Response blocked by safety filters")
                            return _fallback_keyword_extraction(text)
                    
                    # Try to get content from candidate
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            # Extract text from all parts
                            text_parts = []
                            for i, part in enumerate(candidate.content.parts):
                                # Check different ways to get text
                                part_text = None
                                
                                # Method 1: Direct text attribute
                                if hasattr(part, 'text'):
                                    part_text = getattr(part, 'text', None)
                                
                                # Method 2: Check if it's a string-like object
                                if not part_text and isinstance(part, str):
                                    part_text = part
                                
                                # Method 3: Try to convert to string (but filter out object representations)
                                if not part_text:
                                    try:
                                        part_str = str(part)
                                        # Only use if it looks like actual text (not object representation)
                                        if part_str and not part_str.startswith('<') and len(part_str) < 200 and not 'object at 0x' in part_str:
                                            part_text = part_str
                                    except:
                                        pass
                                
                                # Skip non-text parts (images, etc.)
                                if hasattr(part, 'inline_data') and part.inline_data:
                                    continue
                                
                                if part_text:
                                    text_parts.append(part_text)
                                    print(f"      📝 Part {i} extracted: '{part_text[:50]}...'")
                                else:
                                    print(f"      ⚠️  Part {i} could not be extracted: {type(part)}")
                            
                            if text_parts:
                                raw_location = " ".join(text_parts).strip()
                                print(f"      📋 Got response via parts: '{raw_location}'")
                            else:
                                print(f"      ⚠️  Parts found but no text content extracted")
                                # Debug: print part types
                                for i, part in enumerate(candidate.content.parts):
                                    print(f"         Part {i}: type={type(part)}, attrs={dir(part)}")
                    else:
                        print(f"      ⚠️  Candidate has no content or parts")
                        # Try alternative: response.parts directly
                        if hasattr(response, 'parts'):
                            print(f"      🔍 Trying response.parts directly...")
                            text_parts = []
                            for part in response.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_parts.append(part.text)
                            if text_parts:
                                raw_location = " ".join(text_parts).strip()
                                print(f"      📋 Got response via response.parts: '{raw_location}'")
                else:
                    print(f"      ⚠️  No candidates in response")
                    # Try direct parts access as last resort
                    if hasattr(response, 'parts'):
                        text_parts = []
                        for part in response.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        raw_location = " ".join(text_parts).strip()
                        print(f"      📋 Got response via direct parts: '{raw_location}'")
            except Exception as parse_error:
                logger.warning(f"Failed to parse Gemini response parts: {parse_error}")
                print(f"      ⚠️  Could not parse response: {parse_error}")
                import traceback
                traceback.print_exc()
                return _fallback_keyword_extraction(text)
        
        if not raw_location:
            print(f"      ⚠️  Empty response from Gemini, using fallback")
            return _fallback_keyword_extraction(text)
        
        print(f"      📋 Raw Gemini response: '{raw_location}'")
        
        # Clean up the response - remove quotes, explanations, etc.
        location = raw_location.lower().strip()
        
        # Remove common prefixes/suffixes that Gemini might add
        location = re.sub(r'^(location:|the location is:|location:)\s*', '', location, flags=re.IGNORECASE)
        location = location.strip('"\'.,;:!?')
        
        # Remove any trailing explanations (e.g., "mumbai. This is because...")
        # Split by common sentence endings and take first part
        location = re.split(r'[.!?]\s+', location)[0].strip()
        
        # Check if it's a valid location (not just "unknown" or empty)
        if location and location != "unknown" and len(location) > 1:
            # Normalize common variations
            location = _normalize_location(location)
            print(f"      ✅ Gemini extracted location: '{location}'")
            return location
        else:
            print(f"      ⚠️  Gemini returned 'unknown' or empty response")
            # Try fallback keyword matching
            return _fallback_keyword_extraction(text)
            
    except Exception as e:
        logger.error(f"Gemini location extraction failed: {e}")
        print(f"      ❌ Gemini extraction failed: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to keyword matching
        return _fallback_keyword_extraction(text)


def _normalize_location(location: str) -> str:
    """Normalize common location name variations"""
    location = location.lower().strip()
    
    # Common variations
    variations = {
        "bombay": "mumbai",
        "calcutta": "kolkata",
        "madras": "chennai",
        "bangalore": "bangalore",
        "bengaluru": "bangalore",
    }
    
    for variant, normalized in variations.items():
        if variant in location:
            return normalized
    
    return location


def _fallback_keyword_extraction(text: str) -> str:
    """Fallback keyword-based location extraction"""
    if not text:
        return "unknown"
    
    text_lower = text.lower()
    
    # Expanded location keywords with common variations
    location_keywords = {
        # Indian cities
        "mumbai": "mumbai",
        "bombay": "mumbai",
        "delhi": "delhi",
        "new delhi": "delhi",
        "bangalore": "bangalore",
        "bengaluru": "bangalore",
        "chennai": "chennai",
        "madras": "chennai",
        "kolkata": "kolkata",
        "calcutta": "kolkata",
        "hyderabad": "hyderabad",
        "pune": "pune",
        "ahmedabad": "ahmedabad",
        "lucknow": "lucknow",
        "faridabad": "faridabad",
        "dhanori": "pune",  # Dhanori is in Pune
        "iit bombay": "mumbai",
        "iit mumbai": "mumbai",
        # International cities
        "new york": "new york",
        "london": "london",
        "paris": "paris",
        "tokyo": "tokyo",
        "beijing": "beijing",
        # Countries (for tweets mentioning countries)
        "syria": "syria",
        "syrian": "syria",
        "israel": "israel",
        "israeli": "israel",
        "palestine": "palestine",
        "palestinian": "palestine",
        "ukraine": "ukraine",
        "ukrainian": "ukraine",
        "russia": "russia",
        "russian": "russia",
        "pakistan": "pakistan",
        "pakistani": "pakistan",
        "afghanistan": "afghanistan",
        "afghan": "afghanistan",
        "usa": "united states",
        "united states": "united states",
        "america": "united states",
        "american": "united states",
        "china": "china",
        "chinese": "china",
        "india": "india",
        "indian": "india",
    }
    
    # Check for exact matches first (longer strings first)
    sorted_keywords = sorted(location_keywords.items(), key=lambda x: len(x[0]), reverse=True)
    for keyword, location in sorted_keywords:
        if keyword in text_lower:
            print(f"      ✅ Keyword match found: '{keyword}' → '{location}'")
            return location
    
    print(f"      ⚠️  No location keywords found in text")
    return "unknown"


def extract_location_simple(text: str) -> str:
    """
    Simple keyword-based location extraction (fallback)
    
    Args:
        text: Tweet text content
    
    Returns:
        Location string or "unknown"
    """
    text_lower = text.lower()
    
    # Common location patterns
    location_keywords = {
        "mumbai": "mumbai, maharashtra, india",
        "delhi": "delhi, india",
        "bangalore": "bangalore, karnataka, india",
        "chennai": "chennai, tamil nadu, india",
        "kolkata": "kolkata, west bengal, india",
        "hyderabad": "hyderabad, telangana, india",
        "pune": "pune, maharashtra, india",
        "ahmedabad": "ahmedabad, gujarat, india",
        "lucknow": "lucknow, uttar pradesh, india",
        "faridabad": "faridabad, haryana, india",
    }
    
    for keyword, location in location_keywords.items():
        if keyword in text_lower:
            return location
    
    return "unknown"


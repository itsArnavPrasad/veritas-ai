"""
Image analysis service using Google Gemini VLM
"""
import os
import json
import logging
import re
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")


async def analyze_image_description(image_path: Path) -> Dict[str, Any]:
    """
    Analyze image using Gemini VLM to generate detailed factual description
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with description, objects, actions, environment, visible_text, other_details
    """
    if not GEMINI_AVAILABLE:
        raise RuntimeError("Gemini library not available")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables")
    
    try:
        # Import PIL for image handling
        try:
            from PIL import Image as PILImage
        except ImportError:
            raise RuntimeError("Pillow (PIL) not installed. Install with: pip install Pillow")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        prompt = """You are analyzing an uploaded image for a misinformation-detection system.

Provide a precise, factual description of everything visible in the image.

Identify:
- objects
- people (no guessing identities, only describe visible characteristics)
- actions
- environment and background
- any visible printed text (OCR-like)
- any indicators of time, location, or context

Do NOT infer or guess anything that cannot be seen directly.

Return all results as a JSON object with keys:
- "description": A comprehensive factual description of the image
- "objects": List of objects visible in the image
- "actions": List of actions or activities visible
- "environment": Description of the environment/background
- "visible_text": List of any text visible in the image (OCR)
- "other_details": Any other relevant visible details

Return ONLY valid JSON, no additional text or markdown formatting."""

        # Prepare image part
        image = PILImage.open(image_path)
        
        # Generate content with safety settings
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        response = model.generate_content(
            [prompt, image],
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 2000,
                "top_p": 0.8,
            },
            safety_settings=safety_settings
        )
        
        # Extract JSON from response
        response_text = ""
        try:
            response_text = response.text.strip()
        except (ValueError, AttributeError) as e:
            logger.debug(f"response.text failed: {e}, trying parts extraction")
            # Try to extract from parts
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                # Check for finish_reason (safety blocks, etc.)
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason:
                    logger.warning(f"Gemini finish_reason: {candidate.finish_reason}")
                if candidate.content and candidate.content.parts:
                    text_parts = []
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    response_text = " ".join(text_parts).strip()
        
        if not response_text:
            logger.warning("Empty response from Gemini for image description")
            raise RuntimeError("Empty response from Gemini")
        
        logger.debug(f"Raw Gemini response (first 200 chars): {response_text[:200]}")
        
        # Parse JSON response
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Try to find JSON object in the response
        # Look for first { and last }
        first_brace = response_text.find('{')
        last_brace = response_text.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            response_text = response_text[first_brace:last_brace + 1]
        
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as e:
            # If JSON parsing fails, log the error and try to extract what we can
            logger.warning(f"Failed to parse JSON from Gemini response: {e}")
            logger.warning(f"Response text: {response_text[:500]}")
            # Try to extract description at least
            result = {
                "description": response_text if response_text else "Failed to extract description",
                "objects": [],
                "actions": [],
                "environment": "",
                "visible_text": [],
                "other_details": ""
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Gemini image description analysis failed: {e}")
        raise


async def detect_ai_artifacts(image_path: Path) -> Dict[str, Any]:
    """
    Analyze image for AI-generation artifacts using Gemini VLM
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with artifact_detected, confidence, artifacts, explanation
    """
    if not GEMINI_AVAILABLE:
        raise RuntimeError("Gemini library not available")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables")
    
    try:
        # Import PIL for image handling
        try:
            from PIL import Image as PILImage
        except ImportError:
            raise RuntimeError("Pillow (PIL) not installed. Install with: pip install Pillow")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        prompt = """You are an image-forensics model.

Analyze the image for AI-generation artifacts such as:
- extra or missing fingers
- distorted hands or limbs
- melted or unreadable text
- unusual skin texture
- warped reflections or shadows
- anatomically impossible shapes
- inconsistent lighting
- object boundaries that look blurred or duplicated
- repeating texture patterns or unnatural backgrounds

Return a JSON object with:
- "artifact_detected": true/false
- "confidence": A number between 0 and 1 indicating confidence in the detection
- "artifacts": A list of detected issues (empty list if none)
- "explanation": A short summary of your analysis

IMPORTANT: Return ONLY valid JSON, no additional text, no markdown formatting, no code blocks. Start with { and end with }."""

        # Prepare image
        image = PILImage.open(image_path)
        
        # Generate content with safety settings
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        response = model.generate_content(
            [prompt, image],
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 2000,  # Increased to handle longer explanations
                "top_p": 0.8,
            },
            safety_settings=safety_settings
        )
        
        # Extract JSON from response
        response_text = ""
        try:
            response_text = response.text.strip()
        except (ValueError, AttributeError) as e:
            logger.debug(f"response.text failed: {e}, trying parts extraction")
            # Try to extract from parts
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                # Check for finish_reason (safety blocks, etc.)
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason:
                    logger.warning(f"Gemini finish_reason: {candidate.finish_reason}")
                if candidate.content and candidate.content.parts:
                    text_parts = []
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    response_text = " ".join(text_parts).strip()
        
        if not response_text:
            logger.warning("Empty response from Gemini for artifact detection")
            return {
                "artifact_detected": False,
                "confidence": 0.0,
                "artifacts": [],
                "explanation": "Empty response from Gemini"
            }
        
        logger.debug(f"Raw Gemini artifact response (first 200 chars): {response_text[:200]}")
        
        # Parse JSON response
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Try to find JSON object in the response
        # Look for first { and last }
        first_brace = response_text.find('{')
        last_brace = response_text.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            response_text = response_text[first_brace:last_brace + 1]
        
        # Try to parse JSON
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as e:
            # If JSON parsing fails (likely due to truncated response), extract fields using regex
            logger.warning(f"Failed to parse JSON from Gemini artifact detection: {e}")
            logger.debug(f"Response text (first 500 chars): {response_text[:500]}")
            
            # Extract artifact_detected
            artifact_detected = False
            artifact_match = re.search(r'"artifact_detected"\s*:\s*(true|false)', response_text, re.IGNORECASE)
            if artifact_match:
                artifact_detected = artifact_match.group(1).lower() == 'true'
            
            # Extract confidence
            confidence = 0.0
            conf_match = re.search(r'"confidence"\s*:\s*([0-9.]+)', response_text)
            if conf_match:
                try:
                    confidence = float(conf_match.group(1))
                except ValueError:
                    pass
            
            # Extract artifacts array
            artifacts = []
            artifacts_match = re.search(r'"artifacts"\s*:\s*\[(.*?)\]', response_text, re.DOTALL)
            if artifacts_match:
                artifacts_str = artifacts_match.group(1)
                # Extract quoted strings from the array
                artifact_items = re.findall(r'"([^"]*)"', artifacts_str)
                artifacts = artifact_items
            
            # Extract explanation (handle truncated strings)
            explanation = ""
            # First try to match a complete quoted string
            expl_match = re.search(r'"explanation"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', response_text, re.DOTALL)
            if expl_match:
                explanation = expl_match.group(1)
                # Unescape JSON string
                explanation = explanation.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
            else:
                # Try to extract even if truncated - find the start of the explanation value
                expl_start = response_text.find('"explanation"')
                if expl_start != -1:
                    colon_idx = response_text.find(':', expl_start)
                    if colon_idx != -1:
                        # Find the opening quote
                        quote_start = response_text.find('"', colon_idx)
                        if quote_start != -1:
                            # Get everything after the opening quote until the end (might be truncated)
                            explanation = response_text[quote_start + 1:]
                            # Remove trailing incomplete JSON characters
                            explanation = explanation.rstrip('",}').strip()
                            # Unescape if needed
                            explanation = explanation.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
            
            # If we couldn't extract explanation but have other data, provide a default
            if not explanation and (artifact_detected or confidence > 0 or artifacts):
                explanation = "Analysis completed successfully."
            
            result = {
                "artifact_detected": artifact_detected,
                "confidence": confidence,
                "artifacts": artifacts,
                "explanation": explanation
            }
            
            logger.info(f"Extracted partial JSON: artifact_detected={artifact_detected}, confidence={confidence}, artifacts={len(artifacts)}")
        
        # Ensure required fields exist
        if "artifact_detected" not in result:
            result["artifact_detected"] = False
        if "confidence" not in result:
            result["confidence"] = 0.0
        if "artifacts" not in result:
            result["artifacts"] = []
        if "explanation" not in result:
            result["explanation"] = ""
        
        return result
        
    except Exception as e:
        logger.error(f"Gemini AI artifact detection failed: {e}")
        raise

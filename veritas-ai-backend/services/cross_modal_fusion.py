"""
Cross-Modal Fusion Service
Combines text, image, and video analysis results and checks if media relates to text claims
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Google Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")


async def perform_cross_modal_fusion(
    text_analysis: Optional[Dict[str, Any]] = None,
    image_analysis: Optional[Dict[str, Any]] = None,
    video_analysis: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Perform cross-modal fusion analysis using Gemini API
    
    Args:
        text_analysis: Text analysis results from coordinator agent
        image_analysis: Image analysis results (VLM description + artifact analysis)
        video_analysis: Video analysis results (comprehensive video analysis)
        
    Returns:
        Dictionary with fusion results including:
        - content_relevance: Whether image/video relates to text
        - calibrated_verdict: Final verdict combining all modalities
        - fusion_analysis: Detailed analysis from Gemini
        - all_outputs: Combined outputs from all analyses
    """
    if not GEMINI_AVAILABLE:
        raise RuntimeError("Gemini library not available")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        # Prepare text claims summary
        text_summary = ""
        if text_analysis:
            coordinator_output = text_analysis.get("coordinator_output", {})
            comprehensive_answer = coordinator_output.get("comprehensive_answer", "")
            misinformation_analysis = coordinator_output.get("misinformation_analysis", {})
            verdict = misinformation_analysis.get("verdict", "UNKNOWN")
            truth_score = misinformation_analysis.get("overall_truth_score", 0.0)
            
            text_summary = f"""
TEXT ANALYSIS RESULTS:
- Verdict: {verdict}
- Truth Score: {truth_score:.2f}
- Comprehensive Answer: {comprehensive_answer[:500]}...
"""
        
        # Prepare image summary
        image_summary = ""
        if image_analysis:
            vlm_desc = image_analysis.get("vlm_description", {})
            artifact = image_analysis.get("vlm_ai_artifact_analysis", {})
            
            image_summary = f"""
IMAGE ANALYSIS RESULTS:
- Description: {vlm_desc.get("description", "N/A")}
- Objects: {', '.join(vlm_desc.get("objects", [])[:10])}
- Visible Text: {', '.join(vlm_desc.get("visible_text", [])[:5])}
- AI Artifacts Detected: {artifact.get("artifact_detected", False)}
- Artifact Explanation: {artifact.get("explanation", "N/A")}
"""
        
        # Prepare video summary
        video_summary = ""
        if video_analysis:
            video_data = video_analysis.get("video_analysis", {})
            authenticity = video_data.get("authenticity_verdict", "UNCERTAIN")
            auth_score = video_data.get("overall_authenticity_score", 0.0)
            claims = video_data.get("claims", [])
            
            video_summary = f"""
VIDEO ANALYSIS RESULTS:
- Authenticity Verdict: {authenticity}
- Authenticity Score: {auth_score:.2f}
- Video Description: {video_data.get("video_description", "N/A")[:300]}...
- Extracted Claims: {len(claims)} claims
"""
            if claims:
                video_summary += "\nClaims:\n"
                for i, claim in enumerate(claims[:3], 1):
                    video_summary += f"  {i}. {claim.get('claim_text', 'N/A')}\n"
        
        # Build the fusion prompt
        prompt = f"""You are a cross-modal fact-checking fusion system. Your task is to analyze whether the provided image and/or video content is relevant and related to the text claims being verified.

{text_summary}

{image_summary}

{video_summary}

TASK:
1. CONTENT RELEVANCE CHECK:
   - Determine if the image/video content is relevant to the text claims
   - Check if the image/video depicts or relates to what the text claims describe
   - Flag cases where image/video is unrelated (e.g., text about "IIT Bombay bomb blast" but image shows a cat)
   - Provide a relevance score (0.0 = completely unrelated, 1.0 = highly relevant)

2. CALIBRATED VERDICT GENERATION:
   - Combine all three modalities (text, image, video) to generate a final calibrated verdict
   - Consider:
     * Text analysis verdict and truth score
     * Image authenticity (AI artifacts detected)
     * Video authenticity (manipulation indicators)
     * Content relevance between modalities
   - Generate a unified verdict that accounts for all available evidence

3. FUSION ANALYSIS:
   - Provide a detailed explanation of how the modalities relate
   - Note any conflicts or agreements between text, image, and video
   - Explain the reasoning behind the calibrated verdict

OUTPUT FORMAT (JSON):
{{
    "content_relevance": {{
        "is_relevant": true/false,
        "relevance_score": 0.0-1.0,
        "explanation": "Explanation of why image/video is or isn't relevant to text claims"
    }},
    "calibrated_verdict": {{
        "verdict": "LIKELY_TRUE" | "LIKELY_FALSE" | "UNCERTAIN" | "MIXED",
        "confidence": 0.0-1.0,
        "reasoning": "Detailed explanation of the calibrated verdict"
    }},
    "fusion_analysis": {{
        "modalities_agreement": "high" | "medium" | "low" | "conflicting",
        "key_findings": ["finding1", "finding2", ...],
        "conflicts": ["conflict1", "conflict2", ...] or [],
        "supporting_evidence": ["evidence1", "evidence2", ...]
    }},
    "all_outputs": {{
        "text_analysis": {{...text analysis data...}},
        "image_analysis": {{...image analysis data...}} or null,
        "video_analysis": {{...video analysis data...}} or null
    }}
}}

IMPORTANT: Return ONLY valid JSON, no markdown formatting, no code blocks."""

        # Generate content with safety settings
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 4000,
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
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    text_parts = []
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    response_text = " ".join(text_parts).strip()
        
        if not response_text:
            logger.warning("Empty response from Gemini for cross-modal fusion")
            raise RuntimeError("Empty response from Gemini")
        
        logger.debug(f"Raw Gemini fusion response (first 500 chars): {response_text[:500]}")
        
        # Parse JSON response
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Try to find JSON object
        first_brace = response_text.find('{')
        last_brace = response_text.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            response_text = response_text[first_brace:last_brace + 1]
        
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from Gemini fusion response: {e}")
            logger.warning(f"Response text: {response_text[:500]}")
            # Return fallback result
            result = {
                "content_relevance": {
                    "is_relevant": True,
                    "relevance_score": 0.5,
                    "explanation": "Could not parse fusion response"
                },
                "calibrated_verdict": {
                    "verdict": "UNCERTAIN",
                    "confidence": 0.0,
                    "reasoning": "Error parsing fusion analysis"
                },
                "fusion_analysis": {
                    "modalities_agreement": "unknown",
                    "key_findings": [],
                    "conflicts": [],
                    "supporting_evidence": []
                }
            }
        
        # Add all outputs to result
        result["all_outputs"] = {
            "text_analysis": text_analysis,
            "image_analysis": image_analysis,
            "video_analysis": video_analysis
        }
        
        # Add timestamp
        result["fusion_timestamp"] = datetime.utcnow().isoformat()
        
        return result
        
    except Exception as e:
        logger.error(f"Gemini cross-modal fusion failed: {e}")
        raise


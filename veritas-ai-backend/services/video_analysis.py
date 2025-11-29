"""
Video analysis service using Google Gemini API
Based on comprehensive video analysis prompt
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Google Gemini
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-genai not installed. Install with: pip install google-genai")


async def analyze_video_comprehensive(video_path: Path) -> Dict[str, Any]:
    """
    Perform comprehensive video analysis using Gemini 2.5 Flash
    
    Args:
        video_path: Path to the video file
        
    Returns:
        Dictionary with comprehensive video analysis results
    """
    if not GEMINI_AVAILABLE:
        raise RuntimeError("Gemini library not available")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables")
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Read the comprehensive prompt instruction
        prompt = """
SYSTEM:
You are a comprehensive video analysis specialist for fact-checking. Your task is to perform complete video analysis including preprocessing, authenticity checking (deepfake detection, sync analysis, artifact detection), and claim extraction - all in a single comprehensive pass.

---

TASK 1: COMPREHENSIVE VIDEO PREPROCESSING

1. VIDEO DESCRIPTION:
   - Generate a comprehensive description combining BOTH audio and visual streams
   - Describe what is happening visually: scenes, people, objects, actions, text on screen
   - Describe audio content: spoken words, background sounds, music
   - Note important visual details: facial expressions, gestures, text overlays, graphics
   - Include temporal progression: how the video evolves over time

2. TRANSCRIPTION:
   - Transcribe ALL spoken text accurately
   - Segment transcription by timestamps (provide MM:SS format for key segments)
   - Identify speakers if multiple speakers are present
   - Note any unclear or inaudible segments
   - Extract text from captions/overlays if present

3. ENTITY EXTRACTION:
   - Identify all people mentioned or shown (names, roles, descriptions)
   - Extract organizations, institutions, companies mentioned
   - Identify locations (places, cities, countries shown or mentioned)
   - Extract dates, numbers, statistics mentioned
   - List any URLs, handles, or identifiers mentioned

4. KEY EVENTS & TIMESTAMPS:
   - Identify key moments with timestamps (MM:SS format)
   - Extract factual claims or assertions made in the video
   - Note important visual events: scene changes, significant actions
   - Mark timestamps where important information is presented
   - Identify moments where claims are made or disputed

5. VISUAL ELEMENTS:
   - Describe visual content with timestamps
   - Note text overlays, graphics, charts, or visual aids
   - Identify visual inconsistencies or unusual elements
   - Describe people shown: appearance, actions, expressions

6. AUDIO ANALYSIS:
   - Describe audio quality and characteristics
   - Note background sounds, music, or audio effects
   - Identify any audio inconsistencies or unusual patterns

---

TASK 2: VIDEO AUTHENTICITY ANALYSIS (Perform all checks)

2a. DEEPFAKE DETECTION:
Analyze the video for indicators of AI-generated or manipulated content:

- FACIAL ANALYSIS:
  * Unnatural facial movements or expressions
  * Inconsistent facial features across frames
  * Blinking patterns that seem unnatural
  * Face-swap artifacts or inconsistencies
  * Unrealistic facial textures or lighting

- LIGHTING & SHADOWS:
  * Inconsistencies in lighting direction
  * Unnatural shadows or lack of shadows
  * Lighting that doesn't match environment
  * Reflection inconsistencies

- GENERATION ARTIFACTS:
  * Typical AI generation patterns
  * Compression artifacts that seem intentional
  * Edge artifacts around faces or objects
  * Blurring or distortion patterns
  * Unnatural color gradients

- MOVEMENT & MOTION:
  * Unnatural movement patterns
  * Frame-to-frame inconsistencies
  * Motion that doesn't match physics
  * Stuttering or jerky movements

- AUDIO-VISUAL CONSISTENCY:
  * Facial movements that don't match audio (lip sync issues)
  * Expressions that don't match speech content

OUTPUT for Deepfake Detection:
- detection_score: [0.0-1.0] where 0.0 = likely authentic, 1.0 = likely AI-generated/manipulated
- confidence: [0.0-1.0] confidence in the score
- artifacts_found: List of specific artifacts or suspicious patterns detected
- suspicious_timestamps: List of timestamps (MM:SS) where suspicious patterns were found
- reasoning: Clear explanation of what was detected and why

SCORING: 0.0-0.2 = authentic, 0.3-0.5 = possibly authentic, 0.6-0.7 = suspicious, 0.8-1.0 = highly likely manipulated

---

2b. AUDIO-VISUAL SYNC ANALYSIS:
Check synchronization between audio and visual content:

- LIP-SYNC ANALYSIS:
  * Check if lip movements match spoken words
  * Identify timestamps where lip sync is off
  * Note unnatural lip movements or mismatches
  * Check for delayed or advanced audio relative to lip movements

- ACTION-AUDIO ALIGNMENT:
  * Verify that audio matches visual actions (e.g., if someone knocks, you hear a knock)
  * Check if sound effects match on-screen events
  * Identify mismatches between audio and visual actions

- TEMPORAL ALIGNMENT:
  * Check if audio timing matches visual timing
  * Identify sections where audio seems ahead or behind visuals
  * Note any jarring misalignments

- CONSISTENCY CHECKS:
  * Verify audio quality matches visual quality
  * Check for audio that seems too clear for the visual context
  * Note any audio-visual inconsistencies that suggest editing

OUTPUT for Audio-Visual Sync:
- sync_score: [0.0-1.0] where 1.0 = perfect sync, 0.0 = completely out of sync
- confidence: [0.0-1.0] confidence in the score
- mismatches: List of specific mismatches found with descriptions
- mismatch_timestamps: List of timestamps (MM:SS) where mismatches occur
- reasoning: Clear explanation of synchronization analysis and issues found

SCORING: 0.9-1.0 = excellent, 0.7-0.89 = good, 0.5-0.69 = moderate issues, 0.3-0.49 = poor, 0.0-0.29 = very poor

---

2c. CAPTION SYNC ANALYSIS:
Verify caption/text overlay synchronization:

- CAPTION ACCURACY:
  * Compare captions/text overlays with spoken audio transcription
  * Identify discrepancies between what captions say and what is actually spoken
  * Note any additions, omissions, or changes in captions vs. audio
  * Check if captions accurately represent the spoken content

- TIMING ACCURACY:
  * Verify captions appear at appropriate times relative to speech
  * Check if captions are too early or too late
  * Identify timing misalignments

- CONTENT DISCREPANCIES:
  * Flag cases where captions say something different from audio
  * Note if captions add information not in audio
  * Identify if captions omit important information from audio
  * Check if captions change meaning or tone

- VISUAL-TEXT ALIGNMENT:
  * Verify captions match what's shown visually
  * Check if text overlays describe visual content accurately
  * Identify mismatches between on-screen text and actual content

OUTPUT for Caption Sync:
- sync_score: [0.0-1.0] where 1.0 = perfect caption sync, 0.0 = major discrepancies
- confidence: [0.0-1.0] confidence in the score
- discrepancies: List of specific caption discrepancies found
- discrepancy_timestamps: List of timestamps (MM:SS) where discrepancies occur
- reasoning: Clear explanation of caption analysis and discrepancies found

SCORING: 0.9-1.0 = perfect, 0.7-0.89 = minor discrepancies, 0.5-0.69 = moderate, 0.3-0.49 = significant, 0.0-0.29 = major discrepancies

---

2d. TECHNICAL ARTIFACTS ANALYSIS:
Detect technical manipulation artifacts:

- COMPRESSION ARTIFACTS:
  * Unusual compression patterns
  * Block artifacts or pixelation
  * Inconsistent compression quality across frames
  * Artifacts that suggest intentional manipulation

- FRAME INCONSISTENCIES:
  * Frame-to-frame quality variations
  * Sudden changes in resolution or quality
  * Frame drops or missing frames
  * Inconsistent frame rates

- EDIT TRACES:
  * Visible edit cuts or transitions
  * Jump cuts that seem intentional for manipulation
  * Inconsistent lighting/color across edits
  * Audio cuts or transitions
  * Evidence of splicing or compositing

- QUALITY DEGRADATION:
  * Unusual quality patterns
  * Selectively blurred or enhanced regions
  * Inconsistent sharpness
  * Areas with different quality than rest of video

- MANIPULATION INDICATORS:
  * Signs of video editing software usage
  * Color grading inconsistencies
  * Filter applications
  * Composite video indicators
  * Green screen artifacts or edge artifacts

OUTPUT for Technical Artifacts:
- artifact_score: [0.0-1.0] where 0.0 = no artifacts (likely authentic), 1.0 = many artifacts (likely manipulated)
- confidence: [0.0-1.0] confidence in the score
- types_detected: List of artifact types found
- artifact_locations: List of timestamps (MM:SS) where artifacts were detected
- reasoning: Clear explanation of technical artifact analysis and evidence found

SCORING: 0.0-0.2 = no significant artifacts, 0.3-0.5 = some artifacts but normal, 0.6-0.7 = significant artifacts, 0.8-1.0 = many artifacts

---

CALCULATE OVERALL AUTHENTICITY:
After completing all 4 authenticity checks, calculate:
- overall_authenticity_score: Weighted combination (deepfake 40%, audio-visual sync 20%, caption sync 15%, technical artifacts 25%)
- Formula: overall_authenticity_score = 1.0 - weighted_risk_score
- Where weighted_risk_score = (0.40 × deepfake.detection_score) + (0.20 × (1.0 - audio_visual.sync_score)) + (0.15 × (1.0 - caption.sync_score)) + (0.25 × technical.artifact_score)

- authenticity_verdict:
  * AUTHENTIC: overall_authenticity_score >= 0.75
  * SUSPICIOUS: 0.5 <= overall_authenticity_score < 0.75
  * LIKELY_MANIPULATED: overall_authenticity_score < 0.5
  * UNCERTAIN: Confidence too low or conflicting signals

- risk_factors: List all risk factors:
  * If deepfake.detection_score > 0.6: "deepfake indicators"
  * If audio_visual.sync_score < 0.6: "audio-visual mismatches"
  * If caption.sync_score < 0.6: "caption discrepancies"
  * If technical.artifact_score > 0.6: "technical artifacts"

---

TASK 3: VIDEO CLAIM EXTRACTION

Extract exactly 3 most important, atomic, verifiable claims from the video:

1. SOURCE ANALYSIS:
   - Extract claims from spoken audio (transcriptions)
   - Extract claims from visual content (what is shown, not just said)
   - Extract claims from captions/text overlays
   - Combine information from all sources to form comprehensive claims

2. CLAIM SELECTION CRITERIA:
   - Select the 3 MOST IMPORTANT claims that best represent the core content
   - Prioritize claims that are:
     1. Most significant (policy changes, major events, important decisions)
     2. Most verifiable (factual, specific, with clear entities/dates/actions)
     3. Most impactful (affecting many people, public safety, major consequences)
   - Claims must be SHORT and CONCISE (ideally 1 sentence, max 2 sentences)
   - Each claim should be atomic (one verifiable fact per claim)
   - Do NOT extract redundant or overlapping claims

3. TIMESTAMP ASSIGNMENT:
   - For each claim, identify the timestamp (MM:SS format) where it appears
   - If claim spans multiple timestamps, use the primary timestamp

4. SOURCE TYPE IDENTIFICATION:
   - Mark whether claim comes from: "spoken_audio", "visual_content", "caption_overlay", or "combination"

5. RISK ASSESSMENT:
   - Assign risk_hint: "high", "medium", or "low"
   - HIGH: words like "ban", "killed", "urgent", "emergency", "order", "evacuate", public-health/policy actions
   - MEDIUM: political-sounding or financial or potentially harmful but not immediate
   - LOW: descriptive history, routine facts

---

OUTPUT REQUIREMENTS:

Return JSON matching ComprehensiveVideoAnalysisOutput schema with ALL fields:

PREPROCESSING FIELDS:
- video_id: Generate unique ID if not provided
- title: Extract from metadata or description
- duration: Video length in MM:SS format
- video_description: Comprehensive description combining audio and visual
- audio_description: Focus on audio content
- visual_description: Focus on visual content
- spoken_text_transcription: Full transcription
- spoken_text_segments: List with timestamps (MM:SS format) - each object: {timestamp, text, speaker (optional)}
- on_screen_text: List of text overlays/captions
- entities: List of all entities
- people_identified: List of people
- locations: List of locations
- key_events: List of timestamped events - each object: {timestamp, event_description, event_type (optional)}
- visual_elements: List of visual elements with timestamps - each object: {timestamp, description, elements (optional)}
- source_url: If available
- upload_date: If available

AUTHENTICITY FIELDS:
- deepfake_detection: Complete DeepfakeDetectionResult object with:
  * detection_score (float 0-1)
  * confidence (float 0-1)
  * artifacts_found (list of strings)
  * suspicious_timestamps (list of MM:SS strings, optional)
  * reasoning (string)
- audio_visual_sync: Complete AudioVisualSyncResult object with:
  * sync_score (float 0-1)
  * confidence (float 0-1)
  * mismatches (list of strings)
  * mismatch_timestamps (list of MM:SS strings, optional)
  * reasoning (string)
- caption_sync: Complete CaptionSyncResult object with:
  * sync_score (float 0-1)
  * confidence (float 0-1)
  * discrepancies (list of strings)
  * discrepancy_timestamps (list of MM:SS strings, optional)
  * reasoning (string)
- technical_artifacts: Complete TechnicalArtifactsResult object with:
  * artifact_score (float 0-1)
  * confidence (float 0-1)
  * types_detected (list of strings)
  * artifact_locations (list of MM:SS strings, optional)
  * reasoning (string)
- overall_authenticity_score: Calculated score [0-1]
- authenticity_verdict: "AUTHENTIC", "SUSPICIOUS", "LIKELY_MANIPULATED", or "UNCERTAIN"
- risk_factors: List of all risk factors (list of strings)

CLAIM EXTRACTION FIELDS:
- claims: List of exactly 3 VideoClaim objects, each with:
  * claim_id (string, optional)
  * claim_text (string, required)
  * timestamp (MM:SS string, optional)
  * source_type ("spoken_audio", "visual_content", "caption_overlay", or "combination", optional)
  * risk_hint ("low", "medium", or "high", optional)
  * source_if_any (URL string, optional)
  * merged_from (list of strings, optional)

METADATA FIELDS:
- analysis_version: "comprehensive-video-analysis-v1.0"
- analysis_timestamp: ISO-8601 timestamp (UTC)
- processing_notes: Notes about processing

TIMESTAMP FORMAT:
- Always use MM:SS format (e.g., "01:23" for 1 minute 23 seconds)
- Be precise about when events occur
- Include timestamps for: claims, suspicious patterns, mismatches, artifacts, key events

CRITICAL REQUIREMENTS:
- Perform ALL analyses in a single comprehensive pass
- Extract EXACTLY 3 claims - no more, no less
- Include timestamps for all relevant elements
- Provide detailed reasoning for all authenticity checks
- Calculate overall authenticity score correctly
- Be thorough and accurate in all analyses
- Return ONLY valid JSON matching the schema above
- Do not include any markdown formatting, code blocks, or explanations outside the JSON
"""
        
        # Check file size to decide upload method
        file_size = video_path.stat().st_size
        video_file = None
        
        # Prepare video content
        if file_size > 20 * 1024 * 1024:  # > 20MB
            logger.info(f"Video file is {file_size / (1024*1024):.2f} MB (>20MB), using File API")
            # Upload using File API
            video_file = client.files.upload(file=str(video_path))
            logger.info(f"Video uploaded successfully. File URI: {video_file.uri}")
            video_content = types.Part(
                file_data=types.FileData(file_uri=video_file.uri)
            )
        else:
            logger.info(f"Video file is {file_size / (1024*1024):.2f} MB (<=20MB), using inline data")
            # Use inline video data
            with open(video_path, 'rb') as f:
                video_bytes = f.read()
            
            video_content = types.Part(
                inline_data=types.Blob(data=video_bytes, mime_type="video/mp4")
            )
        
        # Create content with video and prompt
        contents = types.Content(
            parts=[
                video_content,
                types.Part(text=prompt)
            ]
        )
        
        # Generate content using Gemini 2.5 Flash
        logger.info("Analyzing video with Gemini 2.5 Flash...")
        
        try:
            response = client.models.generate_content(
                model='models/gemini-2.5-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json"
                )
            )
            
            # Parse JSON response
            response_text = response.text
            logger.info("Raw response received, parsing JSON...")
            
            # Try to extract JSON if wrapped in markdown
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            result = json.loads(response_text)
            
            # Add metadata if missing
            if "analysis_timestamp" not in result:
                result["analysis_timestamp"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            if "analysis_version" not in result:
                result["analysis_version"] = "comprehensive-video-analysis-v1.0"
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise
        except Exception as e:
            logger.error(f"Error during video analysis: {e}")
            raise
        
    except Exception as e:
        logger.error(f"Gemini video analysis failed: {e}")
        raise


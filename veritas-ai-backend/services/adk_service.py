"""
Service for calling Google ADK agents
"""
import os
import json
import re
import requests
import uuid
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Load ADK server URL from environment or use default
ADK_SERVER_URL = os.getenv("ADK_SERVER_URL", "http://localhost:5010")

# Coordinator agent name (based on folder structure)
COORDINATOR_AGENT_NAME = "coordinator"


def call_adk_agent(agent_name: str, input_text: str) -> Dict[str, Any]:
    """
    Call an ADK agent API (session creation + /run request).
    
    Args:
        agent_name: Name of the agent to call (e.g., "coordinator")
        input_text: Text input to send to the agent
        
    Returns:
        Dictionary containing the agent response or error information
    """
    try:
        logger.info(f"Calling {agent_name} at {ADK_SERVER_URL}")

        user_id = "u_backend"
        session_id = f"s_{uuid.uuid4().hex[:8]}"

        # Step 1: Create session
        session_endpoint = f"{ADK_SERVER_URL}/apps/{agent_name}/users/{user_id}/sessions/{session_id}"
        session_payload = {"state": {}}

        session_resp = requests.post(
            session_endpoint,
            json=session_payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )

        if session_resp.status_code != 200:
            logger.error(f"Session creation failed for {agent_name}: {session_resp.status_code} - {session_resp.text}")
            return {
                "error": f"Session creation failed for {agent_name}",
                "details": session_resp.text,
                "status_code": session_resp.status_code
            }

        logger.info(f"Session created for {agent_name}: {session_id}")

        # Step 2: Run with input text
        payload = {
            "app_name": agent_name,
            "user_id": user_id,
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": input_text}]
            }
        }

        run_response = requests.post(
            f"{ADK_SERVER_URL}/run",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=600  # 10 minutes timeout for long-running agents
        )

        if run_response.status_code != 200:
            logger.error(f"{agent_name} run failed: {run_response.status_code} - {run_response.text}")
            return {
                "error": f"{agent_name} run failed",
                "details": run_response.text,
                "status_code": run_response.status_code
            }

        logger.info(f"{agent_name} completed successfully")
        return run_response.json()

    except requests.exceptions.Timeout:
        logger.error(f"{agent_name} request timed out")
        return {"error": f"{agent_name} request timed out"}

    except requests.exceptions.RequestException as e:
        logger.error(f"{agent_name} request failed: {str(e)}")
        return {"error": f"{agent_name} request failed: {str(e)}"}

    except json.JSONDecodeError as e:
        logger.error(f"{agent_name} returned invalid JSON: {str(e)}")
        return {"error": f"{agent_name} returned invalid JSON: {str(e)}"}

    except Exception as e:
        logger.error(f"Unexpected error calling {agent_name}: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}


def extract_json_from_text(data: Any) -> List[Dict[str, Any]]:
    """
    Recursively extract JSON objects from the agent response.
    
    Args:
        data: The response data from the agent
        
    Returns:
        List of extracted JSON objects
    """
    extracted_jsons = []

    def recursive_search(obj):
        if isinstance(obj, dict):
            if 'text' in obj and isinstance(obj['text'], str):
                text_content = obj['text']

                # Try parsing direct JSON
                try:
                    parsed_direct = json.loads(text_content)
                    extracted_jsons.append(parsed_direct)
                except json.JSONDecodeError:
                    # Look for code blocks
                    json_pattern = r'```json\s*\n(.*?)\n```'
                    matches = re.findall(json_pattern, text_content, re.DOTALL)
                    for match in matches:
                        try:
                            parsed_json = json.loads(match)
                            extracted_jsons.append(parsed_json)
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse a JSON block")

            for value in obj.values():
                recursive_search(value)

        elif isinstance(obj, list):
            for item in obj:
                recursive_search(item)

    recursive_search(data)
    return extracted_jsons


def extract_state_delta(agent_response: Any) -> Dict[str, Any]:
    """
    Extract state delta from ADK agent response.
    The agent_response is typically a list of agent outputs, each with stateDelta.
    
    Args:
        agent_response: The response from the ADK agent
        
    Returns:
        Dictionary containing all state deltas merged together
    """
    structured_data = {}
    
    # Parse through the agent response to extract all state deltas
    if isinstance(agent_response, list):
        for entry in agent_response:
            if isinstance(entry, dict) and 'actions' in entry:
                state_delta = entry.get('actions', {}).get('stateDelta', {})
                
                # Merge all state deltas into structured_data
                for key, value in state_delta.items():
                    structured_data[key] = value
    
    # If no data extracted, try the old method as fallback
    if not structured_data:
        extracted_jsons = extract_json_from_text(agent_response)
        if extracted_jsons:
            structured_data = extracted_jsons[0]
    
    return structured_data


def extract_coordinator_output(structured_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract the final coordinator output from structured data.
    The coordinator pipeline outputs various stages, and we want the final verifier_ensemble output.
    
    Args:
        structured_data: The structured data from extract_state_delta
        
    Returns:
        Dictionary containing the final coordinator output (VerifierEnsembleOutput format)
    """
    # The final output should be in verifier_ensemble key
    # But it might also be nested in other keys, so we search for it
    coordinator_output = {}
    
    # Check for verifier_ensemble directly
    if 'verifier_ensemble' in structured_data:
        verifier_data = structured_data['verifier_ensemble']
        if isinstance(verifier_data, dict):
            coordinator_output = verifier_data
        elif isinstance(verifier_data, str):
            # Try to parse as JSON
            try:
                coordinator_output = json.loads(verifier_data)
            except json.JSONDecodeError:
                logger.warning("Could not parse verifier_ensemble as JSON")
    
    # Also check for final_verifier output
    if not coordinator_output and 'final_verifier' in structured_data:
        verifier_data = structured_data['final_verifier']
        if isinstance(verifier_data, dict):
            coordinator_output = verifier_data
        elif isinstance(verifier_data, str):
            try:
                coordinator_output = json.loads(verifier_data)
            except json.JSONDecodeError:
                logger.warning("Could not parse final_verifier as JSON")
    
    # If still not found, look for any key that might contain the final output
    # The output should have keys like: verification_timestamp, comprehensive_answer, individual_claim_findings, etc.
    if not coordinator_output:
        for key, value in structured_data.items():
            if isinstance(value, dict):
                # Check if this looks like the final output
                if any(k in value for k in ['verification_timestamp', 'comprehensive_answer', 'individual_claim_findings', 'misinformation_analysis']):
                    coordinator_output = value
                    break
            elif isinstance(value, str):
                # Try parsing as JSON
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, dict) and any(k in parsed for k in ['verification_timestamp', 'comprehensive_answer', 'individual_claim_findings', 'misinformation_analysis']):
                        coordinator_output = parsed
                        break
                except json.JSONDecodeError:
                    continue
    
    return coordinator_output


async def call_coordinator_agent(text: str) -> Dict[str, Any]:
    """
    Call the coordinator agent with text input.
    
    Args:
        text: The text to analyze
        
    Returns:
        Dictionary containing the coordinator agent's response with final output
    """
    try:
        logger.info(f"Calling coordinator agent with text length: {len(text)}")
        
        # Call the coordinator agent
        agent_response = call_adk_agent(COORDINATOR_AGENT_NAME, text)
        
        if "error" in agent_response:
            return {
                "error": agent_response.get("error"),
                "details": agent_response.get("details"),
                "status": "failed"
            }
        
        # Extract structured data from the response
        structured_data = extract_state_delta(agent_response)
        
        # Extract the final coordinator output (VerifierEnsembleOutput)
        coordinator_output = extract_coordinator_output(structured_data)
        
        return {
            "raw_response": agent_response,
            "structured_data": structured_data,
            "coordinator_output": coordinator_output,
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error calling coordinator agent: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }


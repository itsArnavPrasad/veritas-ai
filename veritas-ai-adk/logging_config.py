"""
Logging configuration for ADK agents.
Suppresses verbose INFO logs from Google ADK library and only shows model outputs.
"""
import logging
import sys

# Configure root logger
logging.basicConfig(
    level=logging.WARNING,  # Only show WARNING and above by default
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

# Suppress verbose logs from Google ADK library
# Set specific loggers to WARNING level to hide INFO messages
adk_loggers = [
    'google.adk',
    'google.adk.agents',
    'google.adk.agents.llm_agent',
    'google.adk.models',
    'google.adk.models.llm_response',
    'google_llm',  # This is the module that logs "Sending out request"
    'google.adk.backends',
    'google.adk.backends.google_llm',
    'google.adk.backends.google_llm.google_llm',  # Full path to the logger
    'google.genai',
    # Also try to catch any logger that might be used
    'google',
]

for logger_name in adk_loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.WARNING)  # Only show WARNING and ERROR

# Keep your own agent logs at INFO level if needed
# Uncomment and modify if you want to see your agent logs
# agent_logger = logging.getLogger('coordinator')
# agent_logger.setLevel(logging.INFO)


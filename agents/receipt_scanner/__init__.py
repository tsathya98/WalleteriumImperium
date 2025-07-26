# Receipt Scanner Agent Module
from .agent import receipt_scanner_agent

# Export the main agent for ADK
__all__ = ["receipt_scanner_agent"]

# Make the agent available as 'root_agent' for ADK
root_agent = receipt_scanner_agent

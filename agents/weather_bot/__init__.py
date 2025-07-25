# Multi-Tool Agent System
from .weather.agent import root_agent as weather_agent

# Export available agents
__all__ = ["weather_agent"]

# Default root agent (you can change this)
root_agent = weather_agent

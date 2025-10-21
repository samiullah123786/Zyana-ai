"""Agent router for main orchestration and commands."""
from fastapi import APIRouter, HTTPException
import logging

from models.schemas import ParsedMessage, AgentResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/execute", response_model=AgentResponse)
async def execute_agent_action(parsed: ParsedMessage, user_id: str):
    """Execute an agent action based on parsed message.
    
    Args:
        parsed: Parsed message with intent and fields
        user_id: User identifier
        
    Returns:
        Agent response with result
    """
    from agents.router import main_agent
    
    try:
        result = await main_agent.route(parsed, user_id=user_id)
        return result
        
    except Exception as e:
        logger.error(f"Error executing agent action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_agent_status():
    """Get agent system status.
    
    Returns:
        System status information
    """
    return {
        "status": "online",
        "agents": {
            "finance": "active",
            "calendar": "active",
            "memory": "active",
            "video": "active",
            "habit_learner": "active"
        }
    }


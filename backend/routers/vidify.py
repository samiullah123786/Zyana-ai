"""Vidify HQ Dashboard API Router.

Provides REST API endpoints for Vidify HQ Dashboard operations.
These can be called directly or through Zyana's natural language interface.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.vidify_dashboard import vidify_agent
from clients.firebase_client import firebase_client

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== REQUEST MODELS ====================

class AddClientRequest(BaseModel):
    name: str
    email: Optional[str] = ""
    company: Optional[str] = ""


class AddProjectRequest(BaseModel):
    name: str
    client_name: str
    amount: Optional[float] = 0


class AddTransactionRequest(BaseModel):
    type: str  # "income" or "expense"
    amount: float
    description: Optional[str] = ""
    category: Optional[str] = "General"
    client_name: Optional[str] = None


class AddTeamMemberRequest(BaseModel):
    name: str
    role: Optional[str] = "Editor"
    salary: Optional[float] = 0
    email: Optional[str] = ""


class PaySalaryRequest(BaseModel):
    member_name: str
    amount: float


class NaturalLanguageRequest(BaseModel):
    """For processing natural language commands."""
    message: str
    user_id: Optional[str] = "default"


# ==================== ENDPOINTS ====================

@router.get("/status")
async def get_vidify_status():
    """Check Vidify HQ connection status."""
    return {
        "connected": firebase_client.is_connected,
        "service": "Vidify HQ Dashboard",
        "description": "Agency management dashboard with clients, projects, and finances"
    }


@router.get("/stats")
async def get_dashboard_stats():
    """Get Vidify HQ dashboard statistics."""
    result = await vidify_agent.get_stats({})
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("response"))
    return result.get("data")


# ==================== CLIENTS ====================

@router.post("/clients")
async def add_client(request: AddClientRequest):
    """Add a new client to Vidify HQ."""
    result = await vidify_agent.add_client({
        "name": request.name,
        "email": request.email,
        "company": request.company
    })
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("response"))
    return result


@router.get("/clients")
async def list_clients(status: Optional[str] = None):
    """List all clients."""
    result = await vidify_agent.list_clients({"status": status})
    return result.get("data", {"clients": []})


# ==================== PROJECTS ====================

@router.post("/projects")
async def add_project(request: AddProjectRequest):
    """Add a new project."""
    result = await vidify_agent.add_project({
        "name": request.name,
        "client_name": request.client_name,
        "amount": request.amount
    })
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("response"))
    return result


@router.get("/projects")
async def list_projects(status: Optional[str] = None):
    """List all projects."""
    result = await vidify_agent.list_projects({"status": status})
    return result.get("data", {"projects": []})


# ==================== TRANSACTIONS ====================

@router.post("/transactions")
async def add_transaction(request: AddTransactionRequest):
    """Add a transaction (income or expense)."""
    if request.type == "income":
        result = await vidify_agent.log_income({
            "amount": request.amount,
            "client_name": request.client_name,
            "description": request.description
        })
    else:
        result = await vidify_agent.log_expense({
            "amount": request.amount,
            "category": request.category,
            "description": request.description
        })
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("response"))
    return result


# ==================== TEAM ====================

@router.post("/team")
async def add_team_member(request: AddTeamMemberRequest):
    """Add a team member."""
    result = await vidify_agent.add_team_member({
        "name": request.name,
        "role": request.role,
        "salary": request.salary,
        "email": request.email
    })
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("response"))
    return result


@router.post("/team/pay-salary")
async def pay_salary(request: PaySalaryRequest):
    """Pay salary to a team member."""
    result = await vidify_agent.pay_salary({
        "member_name": request.member_name,
        "amount": request.amount
    })
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("response"))
    return result


# ==================== NATURAL LANGUAGE ====================

@router.post("/command")
async def process_command(request: NaturalLanguageRequest):
    """Process a natural language command for Vidify.
    
    This endpoint allows direct Vidify commands without going through
    the main intent router. Useful for Vidify-specific integrations.
    """
    from agents.intent_router import intent_router
    
    # Route through intent router
    result = await intent_router.route_intent(
        message=request.message,
        user_id=request.user_id
    )
    
    return result


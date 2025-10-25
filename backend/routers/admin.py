"""Admin dashboard API endpoints."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime, timedelta
import logging

from clients.supabase_client import supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


async def check_admin_access(user_id: int) -> bool:
    """Check if user has admin access.
    
    Args:
        user_id: User ID
        
    Returns:
        True if user is admin
    """
    try:
        result = supabase_client.admin.table("users").select("is_admin").eq(
            "id", user_id
        ).execute()
        
        if result.data:
            return result.data[0].get("is_admin", False)
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking admin access: {e}", exc_info=True)
        return False


@router.get("/stats")
async def get_system_stats():
    """Get overall system statistics.
    
    Returns:
        System stats including totals for all entities
    """
    try:
        # TODO: Get user_id from authentication and check admin access
        user_id = 1
        
        # if not await check_admin_access(user_id):
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get counts
        invoices_result = supabase_client.admin.table("invoices").select(
            "id", count="exact"
        ).execute()
        
        clients_result = supabase_client.admin.table("clients").select(
            "id", count="exact"
        ).execute()
        
        notifications_result = supabase_client.admin.table("scheduled_notifications").select(
            "id", count="exact"
        ).eq("status", "pending").execute()
        
        logs_result = supabase_client.admin.table("agent_logs").select(
            "id", count="exact"
        ).execute()
        
        habits_result = supabase_client.admin.table("habit_profiles").select(
            "id", count="exact"
        ).execute()
        
        # Get pending/overdue payments
        overdue_result = supabase_client.admin.table("invoices").select(
            "id, amount", count="exact"
        ).eq("status", "overdue").execute()
        
        pending_result = supabase_client.admin.table("invoices").select(
            "id, amount", count="exact"
        ).eq("status", "pending").execute()
        
        # Calculate totals
        overdue_amount = sum(float(inv["amount"]) for inv in (overdue_result.data or []))
        pending_amount = sum(float(inv["amount"]) for inv in (pending_result.data or []))
        
        # Get recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_logs = supabase_client.admin.table("agent_logs").select(
            "*"
        ).gte("timestamp", yesterday.isoformat()).order(
            "timestamp", desc=True
        ).limit(10).execute()
        
        stats = {
            "total_invoices": invoices_result.count or 0,
            "total_clients": clients_result.count or 0,
            "pending_notifications": notifications_result.count or 0,
            "total_logs": logs_result.count or 0,
            "habit_profiles": habits_result.count or 0,
            "overdue_invoices": overdue_result.count or 0,
            "overdue_amount": overdue_amount,
            "pending_invoices": pending_result.count or 0,
            "pending_amount": pending_amount,
            "recent_activity": recent_logs.data if recent_logs.data else []
        }
        
        return {
            "success": True,
            "data": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def list_users():
    """List all users (for multi-user setup).
    
    Returns:
        List of users
    """
    try:
        # TODO: Get user_id from authentication and check admin access
        user_id = 1
        
        # if not await check_admin_access(user_id):
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        result = supabase_client.admin.table("users").select("*").execute()
        
        return {
            "success": True,
            "data": result.data if result.data else [],
            "count": len(result.data) if result.data else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_agent_logs(
    limit: int = 50,
    agent_type: str = None,
    status: str = None
):
    """Get recent agent logs with optional filters.
    
    Args:
        limit: Number of logs to return
        agent_type: Filter by agent type
        status: Filter by status
        
    Returns:
        List of agent logs
    """
    try:
        # TODO: Get user_id from authentication and check admin access
        user_id = 1
        
        # if not await check_admin_access(user_id):
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        query = supabase_client.admin.table("agent_logs").select("*")
        
        if agent_type:
            query = query.eq("agent_type", agent_type)
        if status:
            query = query.eq("status", status)
        
        result = query.order("timestamp", desc=True).limit(limit).execute()
        
        return {
            "success": True,
            "data": result.data if result.data else [],
            "count": len(result.data) if result.data else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduled")
async def get_all_scheduled_notifications():
    """Get all scheduled notifications (admin view).
    
    Returns:
        List of all scheduled notifications
    """
    try:
        # TODO: Get user_id from authentication and check admin access
        user_id = 1
        
        # if not await check_admin_access(user_id):
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        result = supabase_client.admin.table("scheduled_notifications").select(
            "*"
        ).order("scheduled_time").execute()
        
        return {
            "success": True,
            "data": result.data if result.data else [],
            "count": len(result.data) if result.data else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scheduled notifications: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/habits")
async def get_all_habit_profiles():
    """Get all habit profiles (admin view).
    
    Returns:
        List of all habit profiles
    """
    try:
        # TODO: Get user_id from authentication and check admin access
        user_id = 1
        
        # if not await check_admin_access(user_id):
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        result = supabase_client.admin.table("habit_profiles").select(
            "*, users(name, telegram_id)"
        ).execute()
        
        return {
            "success": True,
            "data": result.data if result.data else [],
            "count": len(result.data) if result.data else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting habit profiles: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


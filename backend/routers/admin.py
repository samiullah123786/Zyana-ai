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


@router.get("/voice_logs")
async def get_voice_logs(
    limit: int = 50,
    offset: int = 0,
    user_id: int = None,
    start_date: str = None,
    end_date: str = None
):
    """Get voice transcription logs with filtering and pagination.
    
    Args:
        limit: Maximum number of results (default: 50)
        offset: Number of results to skip (default: 0)
        user_id: Optional filter by user ID
        start_date: Optional filter by start date (ISO format)
        end_date: Optional filter by end date (ISO format)
        
    Returns:
        List of voice logs with transcriptions
    """
    try:
        # TODO: Check admin access
        # admin_user_id = 1  # Get from auth
        # if not await check_admin_access(admin_user_id):
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # Build query
        query = supabase_client.admin.table("voice_logs").select(
            "id, user_id, source, file_url, file_size_bytes, duration_seconds, "
            "transcription, language, confidence, model_used, meta, created_at, "
            "users(id, name, telegram_id)"
        )
        
        # Apply filters
        if user_id:
            query = query.eq("user_id", user_id)
        
        if start_date:
            query = query.gte("created_at", start_date)
        
        if end_date:
            query = query.lte("created_at", end_date)
        
        # Order and paginate
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        
        result = query.execute()
        
        logger.info(f"Retrieved {len(result.data) if result.data else 0} voice logs")
        
        return {
            "success": True,
            "data": result.data if result.data else [],
            "count": len(result.data) if result.data else 0,
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice_logs/{log_id}")
async def get_voice_log_detail(log_id: str):
    """Get detailed information for a specific voice log.
    
    Args:
        log_id: Voice log UUID
        
    Returns:
        Detailed voice log with full metadata
    """
    try:
        # TODO: Check admin access
        
        result = supabase_client.admin.table("voice_logs").select(
            "*, users(id, name, telegram_id, email)"
        ).eq("id", log_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Voice log not found")
        
        return {
            "success": True,
            "data": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice log detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice_logs/{log_id}/retranscribe")
async def retranscribe_voice_log(log_id: str):
    """Re-run transcription for a voice log.
    
    Args:
        log_id: Voice log UUID
        
    Returns:
        Updated voice log with new transcription
    """
    try:
        # TODO: Check admin access
        from services.groq_transcriber import groq_transcriber
        import tempfile
        import httpx
        import os
        
        # Get existing log
        result = supabase_client.admin.table("voice_logs").select("*").eq(
            "id", log_id
        ).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Voice log not found")
        
        log = result.data[0]
        
        # Check if we have file_url
        if not log.get("file_url"):
            raise HTTPException(
                status_code=400,
                detail="No file URL available for re-transcription"
            )
        
        # Download audio file
        temp_file = None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(log["file_url"], timeout=30.0)
                response.raise_for_status()
                audio_bytes = response.content
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp:
                temp.write(audio_bytes)
                temp_file = temp.name
            
            # Re-transcribe
            transcription = await groq_transcriber.transcribe_with_groq(temp_file)
            
            if not transcription:
                raise HTTPException(
                    status_code=500,
                    detail="Re-transcription failed"
                )
            
            # Update database
            update_data = {
                "transcription": transcription["text"],
                "language": transcription.get("language"),
                "confidence": transcription.get("confidence"),
                "model_used": transcription.get("model_used"),
                "meta": {
                    **log.get("meta", {}),
                    "retranscribed_at": datetime.now().isoformat(),
                    "previous_transcription": log.get("transcription")
                },
                "updated_at": datetime.now().isoformat()
            }
            
            updated = supabase_client.admin.table("voice_logs").update(
                update_data
            ).eq("id", log_id).execute()
            
            logger.info(f"✅ Re-transcribed voice log: {log_id}")
            
            return {
                "success": True,
                "message": "Voice log re-transcribed successfully",
                "data": updated.data[0] if updated.data else None
            }
            
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error re-transcribing voice log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/voice_logs/{log_id}")
async def delete_voice_log(log_id: str):
    """Delete a voice log.
    
    Args:
        log_id: Voice log UUID
        
    Returns:
        Success message
    """
    try:
        # TODO: Check admin access
        
        # Delete from database
        result = supabase_client.admin.table("voice_logs").delete().eq(
            "id", log_id
        ).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Voice log not found")
        
        logger.info(f"🗑️ Deleted voice log: {log_id}")
        
        return {
            "success": True,
            "message": "Voice log deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting voice log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/full")
async def get_full_health_report():
    """Get comprehensive health report of all agents.
    
    Returns:
        Dict with system status and agent health details
    """
    try:
        from services.health_monitor import health_monitor
        
        logger.info("🏥 Generating full health report...")
        
        report = await health_monitor.run_full_health_check()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "overall_status": report["status"],
            "duration_seconds": report["duration_seconds"],
            "summary": report["summary"],
            "agents": report["agents"],
            "errors": report["errors"]
        }
        
    except Exception as e:
        logger.error(f"Error generating health report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/status")
async def get_system_status():
    """Get quick system status summary.
    
    Returns:
        Dict with overall status and agent counts
    """
    try:
        from services.agent_registry import agent_registry
        
        system_status = agent_registry.get_system_status()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "overall_status": system_status["overall_status"],
            "total_agents": system_status["total_agents"],
            "healthy": system_status["healthy"],
            "degraded": system_status["degraded"],
            "failed": system_status["failed"],
            "unknown": system_status["unknown"]
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/agents")
async def list_all_agents():
    """List all registered agents with their status.
    
    Returns:
        List of agents with metadata
    """
    try:
        from services.agent_registry import agent_registry
        
        agents = agent_registry.list_agents(include_health=True)
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "count": len(agents),
            "agents": agents
        }
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health/check/{agent_name}")
async def check_agent_health(agent_name: str):
    """Run health check on a specific agent.
    
    Args:
        agent_name: Agent name to check
        
    Returns:
        Agent health status
    """
    try:
        from services.health_monitor import health_monitor
        
        result = await health_monitor.check_agent_health(agent_name)
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "status": result["status"],
            "message": result.get("message", ""),
            "dependencies": result.get("dependencies", {})
        }
        
    except Exception as e:
        logger.error(f"Error checking agent health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/logs")
async def get_health_logs(limit: int = 50):
    """Get recent health check logs.
    
    Args:
        limit: Maximum number of logs to return
        
    Returns:
        List of recent health logs
    """
    try:
        result = supabase_client.admin.table("system_health_log").select(
            "*"
        ).order("timestamp", desc=True).limit(limit).execute()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "count": len(result.data) if result.data else 0,
            "logs": result.data or []
        }
        
    except Exception as e:
        logger.error(f"Error getting health logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/summary/daily")
async def get_daily_summaries(days: int = 7):
    """Get daily health summaries.
    
    Args:
        days: Number of days to retrieve
        
    Returns:
        List of daily summaries
    """
    try:
        since_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        
        result = supabase_client.admin.table("daily_health_summary").select(
            "*"
        ).gte("date", since_date).order("date", desc=True).execute()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "count": len(result.data) if result.data else 0,
            "summaries": result.data or []
        }
        
    except Exception as e:
        logger.error(f"Error getting daily summaries: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
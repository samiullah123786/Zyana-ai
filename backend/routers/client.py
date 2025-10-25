"""Client management API endpoints."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import logging

from agents.client_manager import client_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class ClientCreate(BaseModel):
    """Client creation request."""
    name: str
    business_id: int
    contact: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    """Client update request."""
    name: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None


@router.post("/create")
async def create_client(client: ClientCreate):
    """Create a new client.
    
    Args:
        client: Client creation data
        
    Returns:
        Created client data
    """
    try:
        result = await client_manager.create_client(
            name=client.name,
            business_id=client.business_id,
            contact=client.contact,
            email=client.email,
            company=client.company,
            notes=client.notes
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_client endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_clients(
    business_id: Optional[int] = Query(None)
):
    """List clients with optional business filter.
    
    Args:
        business_id: Filter by business
        
    Returns:
        List of clients
    """
    try:
        clients = await client_manager.list_clients(business_id=business_id)
        
        return {
            "success": True,
            "data": clients,
            "count": len(clients)
        }
        
    except Exception as e:
        logger.error(f"Error in list_clients endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{client_id}")
async def get_client(client_id: int):
    """Get client by ID with related data.
    
    Args:
        client_id: Client ID
        
    Returns:
        Client data with invoices
    """
    try:
        client = await client_manager.get_client(client_id)
        
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        return {
            "success": True,
            "data": client
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_client endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{client_id}/status")
async def get_client_status(client_id: int):
    """Get comprehensive client status.
    
    Args:
        client_id: Client ID
        
    Returns:
        Client status with invoice statistics
    """
    try:
        result = await client_manager.get_client_status(client_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_client_status endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{client_id}")
async def update_client(client_id: int, update: ClientUpdate):
    """Update client information.
    
    Args:
        client_id: Client ID
        update: Update data
        
    Returns:
        Updated client data
    """
    try:
        result = await client_manager.update_client(
            client_id=client_id,
            name=update.name,
            contact=update.contact,
            email=update.email,
            company=update.company,
            notes=update.notes
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_client endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{client_id}")
async def delete_client(client_id: int):
    """Delete a client.
    
    Args:
        client_id: Client ID
        
    Returns:
        Success response
    """
    try:
        result = await client_manager.delete_client(client_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_client endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


"""Audit and logging routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.audit import get_audit_db, get_audit_logs, log_action, AuditLog, get_app_state, save_app_state
from app.auth import get_current_user
from app.models import User

router = APIRouter()


@router.get("", response_model=Dict[str, Any])
async def list_audit_logs(
    limit: int = 100,
    offset: int = 0,
    user_id: int = None,
    action: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_audit_db)
):
    """
    List audit logs (admin only).
    
    Args:
        limit: Number of logs to return
        offset: Pagination offset
        user_id: Filter by user ID
        action: Filter by action type
        current_user: Current authenticated user
        db: Audit database session
        
    Returns:
        Audit logs with pagination info
    """
    # Only admins can view audit logs
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    return get_audit_logs(limit=limit, offset=offset, user_id=user_id, action=action)


@router.get("/user/{user_id}", response_model=Dict[str, Any])
async def get_user_audit_logs(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
):
    """
    Get audit logs for a specific user.
    Users can view their own logs, admins can view any user's logs.
    """
    # Users can only view their own logs unless they're admin
    if current_user.id != user_id and "admin" not in current_user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot view other user's logs")
    
    return get_audit_logs(limit=limit, offset=offset, user_id=user_id)


@router.get("/actions/summary", response_model=Dict[str, Any])
async def get_action_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_audit_db)
):
    """
    Get summary of recent actions.
    """
    from sqlalchemy import func
    
    # Get action counts
    actions = db.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).order_by(func.count(AuditLog.id).desc()).all()
    
    action_summary = {action: count for action, count in actions}
    
    # Get status breakdown
    status_counts = db.query(
        AuditLog.status,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.status).all()
    
    status_summary = {status: count for status, count in status_counts}
    
    return {
        "actions": action_summary,
        "status": status_summary,
        "total_logs": db.query(AuditLog).count()
    }


@router.get("/state/{key}")
async def get_state(
    key: str,
    current_user: User = Depends(get_current_user)
):
    """Get stored application state by key."""
    state = get_app_state(key)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State not found")
    return state


@router.post("/state/{key}")
async def save_state(
    key: str,
    value: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Save application state (admin only)."""
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    return save_app_state(key, value)

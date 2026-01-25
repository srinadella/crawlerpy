"""Audit logging and user action tracking."""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

# Audit database setup
AUDIT_DATABASE_URL = "sqlite:///./audit.db"
audit_engine = create_engine(AUDIT_DATABASE_URL, connect_args={"check_same_thread": False})
AuditSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=audit_engine)

Base = declarative_base()


class AuditLog(Base):
    """Audit log for tracking all user actions and system events."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    username = Column(String(255), nullable=True, index=True)
    action = Column(String(255), nullable=False)  # e.g., "crawler_created", "job_started", "search_executed"
    resource_type = Column(String(100), nullable=True)  # e.g., "crawler", "job", "document"
    resource_id = Column(String(255), nullable=True, index=True)
    resource_name = Column(String(255), nullable=True)
    details = Column(JSON, default={})  # Additional context
    status = Column(String(50), default="success")  # success, failure, pending
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "details": self.details,
            "status": self.status,
            "error_message": self.error_message,
            "ip_address": self.ip_address,
        }


class ApplicationState(Base):
    """Persisted application state and settings."""
    __tablename__ = "application_state"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Create tables
Base.metadata.create_all(bind=audit_engine)


def get_audit_db():
    """Get audit database session."""
    db = AuditSessionLocal()
    try:
        yield db
    finally:
        db.close()


def log_action(
    user_id: int = None,
    username: str = None,
    action: str = None,
    resource_type: str = None,
    resource_id: str = None,
    resource_name: str = None,
    details: dict = None,
    status: str = "success",
    error_message: str = None,
    ip_address: str = None,
    user_agent: str = None,
):
    """Log a user action to the audit database."""
    db = AuditSessionLocal()
    try:
        log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            details=details or {},
            status=status,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log)
        db.commit()
        return log.id
    except Exception as e:
        db.rollback()
        print(f"Error logging action: {e}")
    finally:
        db.close()


def get_audit_logs(limit: int = 100, offset: int = 0, user_id: int = None, action: str = None):
    """Retrieve audit logs with optional filtering."""
    db = AuditSessionLocal()
    try:
        query = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        
        logs = query.offset(offset).limit(limit).all()
        total = query.count()
        
        return {
            "logs": [log.to_dict() for log in logs],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    finally:
        db.close()


def save_app_state(key: str, value: any):
    """Save application state."""
    db = AuditSessionLocal()
    try:
        state = db.query(ApplicationState).filter(ApplicationState.key == key).first()
        if state:
            state.value = value
            state.updated_at = datetime.utcnow()
        else:
            state = ApplicationState(key=key, value=value)
            db.add(state)
        db.commit()
        return state.to_dict()
    except Exception as e:
        db.rollback()
        print(f"Error saving app state: {e}")
    finally:
        db.close()


def get_app_state(key: str):
    """Get application state."""
    db = AuditSessionLocal()
    try:
        state = db.query(ApplicationState).filter(ApplicationState.key == key).first()
        return state.to_dict() if state else None
    finally:
        db.close()

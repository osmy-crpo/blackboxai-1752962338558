from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # User information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(100), nullable=True)  # Snapshot in case user is deleted
    user_email = Column(String(255), nullable=True)  # Snapshot in case user is deleted
    
    # Request information
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Action details
    action = Column(String(100), nullable=False, index=True)  # CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT
    resource = Column(String(100), nullable=False, index=True)  # users, products, orders, etc.
    resource_id = Column(String(100), nullable=True)  # ID of the affected resource
    
    # HTTP request details
    method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    endpoint = Column(String(255), nullable=True)
    status_code = Column(Integer, nullable=True)
    
    # Change tracking
    old_values = Column(JSON, nullable=True)  # Previous state (for updates)
    new_values = Column(JSON, nullable=True)  # New state (for creates/updates)
    changes = Column(JSON, nullable=True)     # Summary of what changed
    
    # Additional context
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # security, data, system, user_action
    severity = Column(String(20), default="info")  # info, warning, error, critical
    
    # Business context
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional context-specific data
    tags = Column(JSON, nullable=True)      # Tags for categorization
    
    # Timing
    duration_ms = Column(Integer, nullable=True)  # Request duration in milliseconds
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    warehouse = relationship("Warehouse")
    order = relationship("Order")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', resource='{self.resource}', user_id={self.user_id})>"

class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    
    # Event classification
    event_type = Column(String(100), nullable=False, index=True)  # login_failed, ip_blocked, suspicious_activity
    severity = Column(String(20), nullable=False, index=True)     # low, medium, high, critical
    status = Column(String(20), default="open")                  # open, investigating, resolved, false_positive
    
    # Source information
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # User context (if applicable)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Event details
    description = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    risk_score = Column(Integer, nullable=True)  # 1-100 risk assessment
    
    # Response information
    action_taken = Column(String(100), nullable=True)  # blocked, rate_limited, flagged, etc.
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Timestamps
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    resolver = relationship("User", foreign_keys=[resolved_by])
    
    def __repr__(self):
        return f"<SecurityEvent(id={self.id}, type='{self.event_type}', severity='{self.severity}')>"

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Log classification
    level = Column(String(20), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    logger = Column(String(100), nullable=False)            # Logger name/module
    category = Column(String(50), nullable=True)            # database, api, auth, backup, etc.
    
    # Message details
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # Context information
    function_name = Column(String(100), nullable=True)
    file_name = Column(String(255), nullable=True)
    line_number = Column(Integer, nullable=True)
    
    # Performance metrics
    execution_time = Column(Integer, nullable=True)  # milliseconds
    memory_usage = Column(Integer, nullable=True)    # bytes
    
    # Error information (if applicable)
    exception_type = Column(String(100), nullable=True)
    stack_trace = Column(Text, nullable=True)
    
    # Request context (if applicable)
    request_id = Column(String(100), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<SystemLog(id={self.id}, level='{self.level}', logger='{self.logger}')>"

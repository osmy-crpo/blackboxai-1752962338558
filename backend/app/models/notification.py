from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class NotificationType(str, enum.Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    ALERT = "alert"

class NotificationCategory(str, enum.Enum):
    SYSTEM = "system"
    INVENTORY = "inventory"
    ORDER = "order"
    USER = "user"
    SECURITY = "security"
    WAREHOUSE = "warehouse"
    SUPPLIER = "supplier"
    REPORT = "report"

class NotificationPriority(str, enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class DeliveryMethod(str, enum.Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    
    # Recipient information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)  # For role-based notifications
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)  # For warehouse-specific notifications
    
    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), default=NotificationType.INFO)
    category = Column(Enum(NotificationCategory), default=NotificationCategory.SYSTEM)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL)
    
    # Delivery settings
    delivery_methods = Column(JSON, nullable=True)  # List of delivery methods
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status tracking
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    is_delivered = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Action information
    action_url = Column(String(500), nullable=True)
    action_text = Column(String(100), nullable=True)
    action_data = Column(JSON, nullable=True)
    
    # Reference information
    reference_type = Column(String(50), nullable=True)  # order, product, user, etc.
    reference_id = Column(Integer, nullable=True)
    reference_data = Column(JSON, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Grouping (for batch notifications)
    group_key = Column(String(255), nullable=True)
    is_grouped = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")
    role = relationship("Role")
    warehouse = relationship("Warehouse")
    creator = relationship("User", foreign_keys=[created_by])
    delivery_logs = relationship("NotificationDeliveryLog", back_populates="notification")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, title='{self.title}', type={self.type}, user_id={self.user_id})>"

class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    
    # Template identification
    name = Column(String(255), nullable=False, unique=True)
    code = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Template content
    title_template = Column(String(500), nullable=False)
    message_template = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), default=NotificationType.INFO)
    category = Column(Enum(NotificationCategory), default=NotificationCategory.SYSTEM)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.NORMAL)
    
    # Template settings
    is_active = Column(Boolean, default=True)
    is_system_template = Column(Boolean, default=False)
    supported_languages = Column(JSON, nullable=True)  # List of supported language codes
    
    # Default delivery settings
    default_delivery_methods = Column(JSON, nullable=True)
    auto_expire_hours = Column(Integer, nullable=True)
    
    # Template variables documentation
    variables = Column(JSON, nullable=True)  # Documentation of available variables
    sample_data = Column(JSON, nullable=True)  # Sample data for testing
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    creator = relationship("User")
    
    def __repr__(self):
        return f"<NotificationTemplate(id={self.id}, name='{self.name}', code='{self.code}')>"

class NotificationDeliveryLog(Base):
    __tablename__ = "notification_delivery_logs"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    
    # Delivery details
    delivery_method = Column(Enum(DeliveryMethod), nullable=False)
    recipient = Column(String(255), nullable=False)  # email address, phone number, etc.
    
    # Status
    status = Column(String(50), nullable=False)  # pending, sent, delivered, failed, bounced
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    
    # Response information
    provider_response = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timing
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    notification = relationship("Notification", back_populates="delivery_logs")
    
    def __repr__(self):
        return f"<NotificationDeliveryLog(id={self.id}, notification_id={self.notification_id}, method={self.delivery_method}, status='{self.status}')>"

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Preference settings
    category = Column(Enum(NotificationCategory), nullable=False)
    type = Column(Enum(NotificationType), nullable=True)  # If null, applies to all types in category
    
    # Delivery method preferences
    in_app_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    
    # Timing preferences
    quiet_hours_start = Column(String(5), nullable=True)  # HH:MM format
    quiet_hours_end = Column(String(5), nullable=True)    # HH:MM format
    timezone = Column(String(50), nullable=True)
    
    # Frequency settings
    digest_enabled = Column(Boolean, default=False)
    digest_frequency = Column(String(20), nullable=True)  # daily, weekly, monthly
    digest_time = Column(String(5), nullable=True)        # HH:MM format
    
    # Priority filtering
    min_priority = Column(Enum(NotificationPriority), default=NotificationPriority.LOW)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<NotificationPreference(id={self.id}, user_id={self.user_id}, category={self.category})>"

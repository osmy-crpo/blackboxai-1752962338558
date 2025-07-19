from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json

from app.models.notification import (
    Notification, 
    NotificationTemplate, 
    NotificationDeliveryLog,
    NotificationPreference,
    NotificationType,
    NotificationCategory,
    NotificationPriority,
    DeliveryMethod
)
from app.models.user import User, Role
from app.models.warehouse import Warehouse
from app.schemas.notification import NotificationCreate
from app.services.base_service import BaseService
from app.core.config import settings

class NotificationService(BaseService[Notification, NotificationCreate, dict]):
    def __init__(self, db: AsyncSession):
        super().__init__(Notification, db)
    
    async def create_notification(
        self,
        title: str,
        message: str,
        user_id: Optional[int] = None,
        role_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        notification_type: NotificationType = NotificationType.INFO,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        delivery_methods: Optional[List[str]] = None,
        scheduled_for: Optional[datetime] = None,
        expires_at: Optional[datetime] = None
    ) -> Notification:
        """Create a new notification."""
        
        notification = Notification(
            user_id=user_id,
            role_id=role_id,
            warehouse_id=warehouse_id,
            title=title,
            message=message,
            type=notification_type,
            category=category,
            priority=priority,
            action_url=action_url,
            action_text=action_text,
            reference_type=reference_type,
            reference_id=reference_id,
            metadata=metadata,
            delivery_methods=delivery_methods,
            scheduled_for=scheduled_for,
            expires_at=expires_at
        )
        
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        
        # Schedule delivery if not scheduled for later
        if not scheduled_for or scheduled_for <= datetime.utcnow():
            await self.deliver_notification(notification.id)
        
        return notification
    
    async def create_from_template(
        self,
        template_code: str,
        variables: Dict[str, Any],
        user_id: Optional[int] = None,
        role_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        **kwargs
    ) -> Optional[Notification]:
        """Create notification from template."""
        
        # Get template
        template = await self.get_template_by_code(template_code)
        if not template:
            return None
        
        # Render template
        title = self.render_template(template.title_template, variables)
        message = self.render_template(template.message_template, variables)
        
        # Create notification
        return await self.create_notification(
            title=title,
            message=message,
            user_id=user_id,
            role_id=role_id,
            warehouse_id=warehouse_id,
            notification_type=template.type,
            category=template.category,
            priority=template.priority,
            delivery_methods=template.default_delivery_methods,
            expires_at=datetime.utcnow() + timedelta(hours=template.auto_expire_hours) if template.auto_expire_hours else None,
            **kwargs
        )
    
    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        category: Optional[NotificationCategory] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Get notifications for a specific user."""
        
        stmt = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)
        
        if category:
            stmt = stmt.where(Notification.category == category)
        
        # Filter out expired notifications
        stmt = stmt.where(
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )
        
        stmt = stmt.order_by(Notification.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_role_notifications(
        self,
        role_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Get notifications for a specific role."""
        
        stmt = select(Notification).where(Notification.role_id == role_id)
        
        # Filter out expired notifications
        stmt = stmt.where(
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )
        
        stmt = stmt.order_by(Notification.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read."""
        
        notification = await self.get(notification_id)
        if not notification or notification.user_id != user_id:
            return False
        
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        await self.db.commit()
        return True
    
    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user."""
        
        stmt = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        result = await self.db.execute(stmt)
        notifications = result.scalars().all()
        
        count = 0
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            count += 1
        
        await self.db.commit()
        return count
    
    async def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user."""
        
        stmt = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False,
                or_(
                    Notification.expires_at.is_(None),
                    Notification.expires_at > datetime.utcnow()
                )
            )
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())
    
    async def deliver_notification(self, notification_id: int) -> bool:
        """Deliver notification through configured channels."""
        
        notification = await self.get(notification_id)
        if not notification:
            return False
        
        # Get delivery methods
        delivery_methods = notification.delivery_methods or [DeliveryMethod.IN_APP]
        
        success = True
        for method in delivery_methods:
            try:
                if method == DeliveryMethod.IN_APP:
                    # In-app notifications are already created
                    await self.log_delivery(notification_id, method, "delivered", "In-app notification created")
                elif method == DeliveryMethod.EMAIL:
                    await self.send_email_notification(notification)
                elif method == DeliveryMethod.SMS:
                    await self.send_sms_notification(notification)
                elif method == DeliveryMethod.PUSH:
                    await self.send_push_notification(notification)
            except Exception as e:
                success = False
                await self.log_delivery(notification_id, method, "failed", str(e))
        
        # Update notification status
        notification.is_sent = True
        notification.sent_at = datetime.utcnow()
        if success:
            notification.is_delivered = True
            notification.delivered_at = datetime.utcnow()
        
        await self.db.commit()
        return success
    
    async def send_email_notification(self, notification: Notification) -> bool:
        """Send email notification."""
        # This is a placeholder - implement actual email sending
        # You would integrate with your email service here
        
        if not notification.user_id:
            return False
        
        user = await self.db.get(User, notification.user_id)
        if not user or not user.email:
            return False
        
        # Log the delivery attempt
        await self.log_delivery(
            notification.id, 
            DeliveryMethod.EMAIL, 
            "sent", 
            f"Email sent to {user.email}",
            recipient=user.email
        )
        
        return True
    
    async def send_sms_notification(self, notification: Notification) -> bool:
        """Send SMS notification."""
        # This is a placeholder - implement actual SMS sending
        
        if not notification.user_id:
            return False
        
        user = await self.db.get(User, notification.user_id)
        if not user or not user.phone:
            return False
        
        # Log the delivery attempt
        await self.log_delivery(
            notification.id, 
            DeliveryMethod.SMS, 
            "sent", 
            f"SMS sent to {user.phone}",
            recipient=user.phone
        )
        
        return True
    
    async def send_push_notification(self, notification: Notification) -> bool:
        """Send push notification."""
        # This is a placeholder - implement actual push notification sending
        
        await self.log_delivery(
            notification.id, 
            DeliveryMethod.PUSH, 
            "sent", 
            "Push notification sent"
        )
        
        return True
    
    async def send_password_reset_email(self, email: str, reset_token: str) -> bool:
        """Send password reset email."""
        # This is a placeholder for password reset email
        # In a real implementation, you would send an actual email
        
        return True
    
    async def log_delivery(
        self,
        notification_id: int,
        method: DeliveryMethod,
        status: str,
        message: str,
        recipient: Optional[str] = None
    ) -> NotificationDeliveryLog:
        """Log notification delivery attempt."""
        
        log = NotificationDeliveryLog(
            notification_id=notification_id,
            delivery_method=method,
            recipient=recipient or "unknown",
            status=status,
            attempts=1,
            provider_response={"message": message} if message else None
        )
        
        if status == "sent":
            log.sent_at = datetime.utcnow()
        elif status == "delivered":
            log.delivered_at = datetime.utcnow()
        elif status == "failed":
            log.failed_at = datetime.utcnow()
            log.error_message = message
        
        self.db.add(log)
        await self.db.commit()
        return log
    
    async def get_template_by_code(self, code: str) -> Optional[NotificationTemplate]:
        """Get notification template by code."""
        
        stmt = select(NotificationTemplate).where(
            and_(
                NotificationTemplate.code == code,
                NotificationTemplate.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render template with variables."""
        # Simple template rendering - in production you might use Jinja2
        
        rendered = template
        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            rendered = rendered.replace(placeholder, str(value))
        
        return rendered
    
    async def create_system_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> List[Notification]:
        """Create system-wide notification for all active users."""
        
        # Get all active users
        stmt = select(User).where(User.is_active == True)
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        notifications = []
        for user in users:
            notification = await self.create_notification(
                title=title,
                message=message,
                user_id=user.id,
                notification_type=notification_type,
                category=NotificationCategory.SYSTEM,
                priority=priority
            )
            notifications.append(notification)
        
        return notifications
    
    async def create_low_stock_alert(
        self,
        product_name: str,
        current_stock: int,
        min_stock: int,
        warehouse_name: str,
        warehouse_id: int
    ) -> List[Notification]:
        """Create low stock alert notifications."""
        
        # Get warehouse managers and inventory staff
        stmt = select(User).join(User.roles).where(
            Role.name.in_(["warehouse_manager", "inventory_manager"])
        )
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        notifications = []
        for user in users:
            notification = await self.create_notification(
                title=f"Low Stock Alert - {product_name}",
                message=f"Product {product_name} in {warehouse_name} is running low. Current stock: {current_stock}, Minimum: {min_stock}",
                user_id=user.id,
                warehouse_id=warehouse_id,
                notification_type=NotificationType.WARNING,
                category=NotificationCategory.INVENTORY,
                priority=NotificationPriority.HIGH,
                reference_type="product",
                reference_id=None  # You would pass product_id here
            )
            notifications.append(notification)
        
        return notifications
    
    async def cleanup_expired_notifications(self) -> int:
        """Clean up expired notifications."""
        
        stmt = select(Notification).where(
            and_(
                Notification.expires_at.is_not(None),
                Notification.expires_at < datetime.utcnow()
            )
        )
        result = await self.db.execute(stmt)
        expired_notifications = result.scalars().all()
        
        count = 0
        for notification in expired_notifications:
            await self.db.delete(notification)
            count += 1
        
        await self.db.commit()
        return count

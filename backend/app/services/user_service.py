from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime

from app.models.user import User, Role, Permission, UserRole
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, generate_password
from app.services.base_service import BaseService

class UserService(BaseService[User, UserCreate, UserUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user with roles."""
        # Check if username or email already exists
        existing_user = await self.get_by_username_or_email(
            user_data.username, 
            user_data.email
        )
        if existing_user:
            raise ValueError("Username or email already exists")
        
        # Create user
        user_dict = user_data.dict(exclude={'password', 'confirm_password', 'role_ids'})
        user_dict['hashed_password'] = get_password_hash(user_data.password)
        
        user = User(**user_dict)
        self.db.add(user)
        await self.db.flush()  # Get user ID
        
        # Assign roles
        if user_data.role_ids:
            await self.assign_roles(user.id, user_data.role_ids)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_by_username_or_email(self, username: str, email: str) -> Optional[User]:
        """Get user by username or email."""
        stmt = select(User).where(
            or_(User.username == username, User.email == email)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_with_roles(self, user_id: int) -> Optional[User]:
        """Get user with roles and permissions."""
        stmt = select(User).options(
            selectinload(User.roles).selectinload(Role.permissions)
        ).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user with role assignment."""
        user = await self.get(user_id)
        if not user:
            return None
        
        # Update user fields
        update_dict = user_data.dict(exclude_unset=True, exclude={'role_ids'})
        for field, value in update_dict.items():
            setattr(user, field, value)
        
        # Update roles if provided
        if user_data.role_ids is not None:
            await self.assign_roles(user_id, user_data.role_ids)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def change_password(self, user_id: int, new_password: str) -> bool:
        """Change user password."""
        user = await self.get(user_id)
        if not user:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        user.password_changed_at = datetime.utcnow()
        await self.db.commit()
        return True
    
    async def reset_password_with_token(self, token: str, new_password: str) -> bool:
        """Reset password using reset token."""
        # This is a simplified implementation
        # In production, you would store reset tokens in database or cache
        # and verify them properly
        
        # For now, return False as token verification is not implemented
        return False
    
    async def assign_roles(self, user_id: int, role_ids: List[int]) -> bool:
        """Assign roles to user."""
        # Remove existing role assignments
        stmt = select(UserRole).where(UserRole.user_id == user_id)
        result = await self.db.execute(stmt)
        existing_assignments = result.scalars().all()
        
        for assignment in existing_assignments:
            await self.db.delete(assignment)
        
        # Add new role assignments
        for role_id in role_ids:
            assignment = UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by=user_id  # In real app, this would be current user
            )
            self.db.add(assignment)
        
        await self.db.commit()
        return True
    
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """Get all permissions for a user."""
        user = await self.get_with_roles(user_id)
        if not user:
            return []
        
        permissions = set()
        for role in user.roles:
            for permission in role.permissions:
                permissions.add(f"{permission.resource}:{permission.action}")
        
        return list(permissions)
    
    async def has_permission(self, user_id: int, resource: str, action: str) -> bool:
        """Check if user has specific permission."""
        permissions = await self.get_user_permissions(user_id)
        return f"{resource}:{action}" in permissions
    
    async def activate_user(self, user_id: int) -> bool:
        """Activate user account."""
        user = await self.get(user_id)
        if not user:
            return False
        
        user.is_active = True
        await self.db.commit()
        return True
    
    async def deactivate_user(self, user_id: int) -> bool:
        """Deactivate user account."""
        user = await self.get(user_id)
        if not user:
            return False
        
        user.is_active = False
        await self.db.commit()
        return True
    
    async def verify_user(self, user_id: int) -> bool:
        """Verify user account."""
        user = await self.get(user_id)
        if not user:
            return False
        
        user.is_verified = True
        await self.db.commit()
        return True
    
    async def search_users(
        self, 
        query: str, 
        is_active: Optional[bool] = None,
        role_id: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[User]:
        """Search users with filters."""
        stmt = select(User).options(selectinload(User.roles))
        
        # Add search filter
        if query:
            search_filter = or_(
                User.username.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%"),
                User.first_name.ilike(f"%{query}%"),
                User.last_name.ilike(f"%{query}%")
            )
            stmt = stmt.where(search_filter)
        
        # Add active filter
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        
        # Add role filter
        if role_id:
            stmt = stmt.join(User.roles).where(Role.id == role_id)
        
        # Add pagination
        stmt = stmt.offset(offset).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_users_by_role(self, role_name: str) -> List[User]:
        """Get all users with specific role."""
        stmt = select(User).join(User.roles).where(Role.name == role_name)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def bulk_update_users(self, user_ids: List[int], update_data: dict) -> int:
        """Bulk update multiple users."""
        stmt = select(User).where(User.id.in_(user_ids))
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        updated_count = 0
        for user in users:
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
                    updated_count += 1
        
        await self.db.commit()
        return updated_count
    
    async def get_user_stats(self) -> dict:
        """Get user statistics."""
        total_users = await self.count()
        
        # Active users
        stmt = select(User).where(User.is_active == True)
        result = await self.db.execute(stmt)
        active_users = len(result.scalars().all())
        
        # Verified users
        stmt = select(User).where(User.is_verified == True)
        result = await self.db.execute(stmt)
        verified_users = len(result.scalars().all())
        
        # Users with 2FA
        stmt = select(User).where(User.is_2fa_enabled == True)
        result = await self.db.execute(stmt)
        users_with_2fa = len(result.scalars().all())
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "users_with_2fa": users_with_2fa,
            "inactive_users": total_users - active_users
        }

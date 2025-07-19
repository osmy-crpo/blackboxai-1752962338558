from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user_token
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfile,
    ChangePassword
)
from app.schemas.common import (
    PaginationParams,
    PaginatedResponse,
    MessageResponse,
    BulkOperationResponse
)
from app.services.user_service import UserService
from app.services.audit_service import AuditService

router = APIRouter()

@router.get("/me", response_model=UserProfile)
async def get_current_user(
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Get current user profile."""
    user_service = UserService(db)
    user = await user_service.get_with_roles(int(current_user_id))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfile(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        language=user.language,
        timezone=user.timezone,
        is_2fa_enabled=user.is_2fa_enabled,
        last_login=user.last_login,
        created_at=user.created_at
    )

@router.put("/me", response_model=UserProfile)
async def update_current_user(
    user_update: UserUpdate,
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile."""
    user_service = UserService(db)
    
    # Don't allow role updates through this endpoint
    user_update.role_ids = None
    
    user = await user_service.update_user(int(current_user_id), user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfile(
        id=user.id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        avatar_url=user.avatar_url,
        language=user.language,
        timezone=user.timezone,
        is_2fa_enabled=user.is_2fa_enabled,
        last_login=user.last_login,
        created_at=user.created_at
    )

@router.post("/change-password", response_model=MessageResponse)
async def change_user_password(
    password_data: ChangePassword,
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Change current user password."""
    user_service = UserService(db)
    
    # Verify current password
    user = await user_service.get(int(current_user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    from app.core.security import verify_password
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Change password
    success = await user_service.change_password(int(current_user_id), password_data.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )
    
    return MessageResponse(message="Password changed successfully")

@router.get("/", response_model=PaginatedResponse[UserResponse])
async def get_users(
    pagination: PaginationParams = Depends(),
    is_active: Optional[bool] = Query(None),
    role_id: Optional[int] = Query(None),
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Get all users with pagination and filtering."""
    user_service = UserService(db)
    
    # Check permissions (implement permission checking)
    # For now, allow all authenticated users
    
    result = await user_service.get_paginated(
        page=pagination.page,
        size=pagination.size,
        search_query=pagination.search,
        search_fields=["username", "email", "first_name", "last_name"],
        filters={
            "is_active": is_active,
        } if is_active is not None else None,
        order_by=pagination.sort_by or "created_at",
        order_desc=pagination.sort_order == "desc"
    )
    
    return PaginatedResponse[UserResponse](
        items=[UserResponse.from_orm(user) for user in result["items"]],
        total=result["total"],
        page=result["page"],
        size=result["size"],
        pages=result["pages"],
        has_next=result["has_next"],
        has_prev=result["has_prev"]
    )

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Create a new user."""
    user_service = UserService(db)
    
    # Check permissions (implement permission checking)
    # For now, allow all authenticated users
    
    try:
        user = await user_service.create_user(user_data)
        return UserResponse.from_orm(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID."""
    user_service = UserService(db)
    
    user = await user_service.get_with_roles(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Update user by ID."""
    user_service = UserService(db)
    
    # Check permissions (implement permission checking)
    # For now, allow all authenticated users
    
    user = await user_service.update_user(user_id, user_update)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)

@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Delete user by ID."""
    user_service = UserService(db)
    
    # Check permissions (implement permission checking)
    # Prevent self-deletion
    if int(current_user_id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    success = await user_service.delete(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return MessageResponse(message="User deleted successfully")

@router.post("/{user_id}/activate", response_model=MessageResponse)
async def activate_user(
    user_id: int,
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Activate user account."""
    user_service = UserService(db)
    
    success = await user_service.activate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return MessageResponse(message="User activated successfully")

@router.post("/{user_id}/deactivate", response_model=MessageResponse)
async def deactivate_user(
    user_id: int,
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate user account."""
    user_service = UserService(db)
    
    # Prevent self-deactivation
    if int(current_user_id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    success = await user_service.deactivate_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return MessageResponse(message="User deactivated successfully")

@router.get("/search/{query}", response_model=List[UserResponse])
async def search_users(
    query: str,
    is_active: Optional[bool] = Query(None),
    role_id: Optional[int] = Query(None),
    limit: int = Query(20, le=100),
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Search users."""
    user_service = UserService(db)
    
    users = await user_service.search_users(
        query=query,
        is_active=is_active,
        role_id=role_id,
        limit=limit
    )
    
    return [UserResponse.from_orm(user) for user in users]

@router.get("/stats/overview")
async def get_user_stats(
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics."""
    user_service = UserService(db)
    
    stats = await user_service.get_user_stats()
    return stats

@router.post("/bulk/update", response_model=BulkOperationResponse)
async def bulk_update_users(
    user_ids: List[int],
    update_data: dict,
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """Bulk update users."""
    user_service = UserService(db)
    
    # Check permissions and validate update_data
    allowed_fields = ["is_active", "language", "timezone"]
    filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    if not filtered_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    updated_count = await user_service.bulk_update_users(user_ids, filtered_data)
    
    return BulkOperationResponse(
        success_count=updated_count,
        error_count=len(user_ids) - updated_count,
        total_count=len(user_ids),
        message=f"Updated {updated_count} users successfully"
    )

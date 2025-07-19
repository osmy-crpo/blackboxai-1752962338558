from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_client_ip,
    generate_totp_secret,
    generate_totp_qr_code,
    verify_totp_token,
    generate_password
)
from app.core.config import settings
from app.models.user import User
from app.models.audit import AuditLog, SecurityEvent
from app.schemas.user import (
    UserLogin,
    Token,
    RefreshToken,
    UserProfile,
    ChangePassword,
    ResetPassword,
    Enable2FA,
    Verify2FA,
    Setup2FAResponse,
    Disable2FA
)
from app.schemas.common import MessageResponse
from app.services.user_service import UserService
from app.services.notification_service import NotificationService

router = APIRouter()
security = HTTPBearer()
limiter = Limiter(key_func=get_remote_address)

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    - **username**: Username or email address
    - **password**: User password
    - **remember_me**: Extended token expiration
    - **totp_code**: TOTP code if 2FA is enabled
    """
    client_ip = get_client_ip(request)
    
    # Get user by username or email
    stmt = select(User).where(
        (User.username == user_credentials.username) | 
        (User.email == user_credentials.username)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # Check if user exists and password is correct
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        # Log failed login attempt
        await log_security_event(
            db, "login_failed", "medium", client_ip,
            f"Failed login attempt for username: {user_credentials.username}",
            user_id=user.id if user else None
        )
        
        # Increment failed attempts if user exists
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check if account is active
    if not user.is_active:
        await log_security_event(
            db, "login_blocked", "medium", client_ip,
            f"Login attempt on inactive account: {user.username}",
            user_id=user.id
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        await log_security_event(
            db, "login_blocked", "medium", client_ip,
            f"Login attempt on locked account: {user.username}",
            user_id=user.id
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Account is locked until {user.locked_until}"
        )
    
    # Check 2FA if enabled
    if user.is_2fa_enabled:
        if not user_credentials.totp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP code required for 2FA"
            )
        
        if not verify_totp_token(user.totp_secret, user_credentials.totp_code):
            await log_security_event(
                db, "2fa_failed", "high", client_ip,
                f"Failed 2FA attempt for user: {user.username}",
                user_id=user.id
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid TOTP code"
            )
    
    # Reset failed attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    
    # Create tokens
    token_expiry = timedelta(days=7) if user_credentials.remember_me else None
    access_token = create_access_token(user.id, token_expiry)
    refresh_token = create_refresh_token(user.id)
    
    await db.commit()
    
    # Log successful login
    await log_audit_event(
        db, user.id, "LOGIN", "auth", None, client_ip,
        "User logged in successfully"
    )
    
    # Create user profile response
    user_profile = UserProfile(
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
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_profile
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshToken,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    """
    user_id = verify_token(refresh_data.refresh_token, "refresh")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user
    user = await db.get(User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    
    # Create user profile response
    user_profile = UserProfile(
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
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_profile
    )

@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user (client should discard tokens).
    """
    client_ip = get_client_ip(request)
    
    # Log logout event
    await log_audit_event(
        db, int(current_user_id), "LOGOUT", "auth", None, client_ip,
        "User logged out"
    )
    
    return MessageResponse(message="Successfully logged out")

@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    password_data: ChangePassword,
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password.
    """
    user = await db.get(User, int(current_user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    user_service = UserService(db)
    await user_service.change_password(user.id, password_data.new_password)
    
    return MessageResponse(message="Password changed successfully")

@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Send password reset email.
    """
    # Get user by email
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user and user.is_active:
        # Generate reset token (implement token generation logic)
        reset_token = generate_password(32)
        
        # Send reset email (implement email service)
        notification_service = NotificationService(db)
        await notification_service.send_password_reset_email(user.email, reset_token)
    
    # Always return success to prevent email enumeration
    return MessageResponse(message="If the email exists, a reset link has been sent")

@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    reset_data: ResetPassword,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using reset token.
    """
    # Verify reset token (implement token verification logic)
    # This is a simplified implementation
    user_service = UserService(db)
    success = await user_service.reset_password_with_token(
        reset_data.token, 
        reset_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return MessageResponse(message="Password reset successfully")

# 2FA Endpoints
@router.post("/2fa/setup", response_model=Setup2FAResponse)
async def setup_2fa(
    setup_data: Enable2FA,
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Setup 2FA for user account.
    """
    user = await db.get(User, int(current_user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify password
    if not verify_password(setup_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )
    
    # Generate TOTP secret and QR code
    secret = generate_totp_secret()
    qr_code = generate_totp_qr_code(user.email, secret)
    
    # Generate backup codes
    backup_codes = [generate_password(8) for _ in range(10)]
    
    # Store secret (don't enable 2FA yet)
    user.totp_secret = secret
    await db.commit()
    
    return Setup2FAResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes
    )

@router.post("/2fa/verify", response_model=MessageResponse)
async def verify_2fa_setup(
    verify_data: Verify2FA,
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify and enable 2FA.
    """
    user = await db.get(User, int(current_user_id))
    if not user or not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA setup not initiated"
        )
    
    # Verify TOTP code
    if not verify_totp_token(user.totp_secret, verify_data.totp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code"
        )
    
    # Enable 2FA
    user.is_2fa_enabled = True
    await db.commit()
    
    return MessageResponse(message="2FA enabled successfully")

@router.post("/2fa/disable", response_model=MessageResponse)
async def disable_2fa(
    disable_data: Disable2FA,
    current_user_id: str = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Disable 2FA for user account.
    """
    user = await db.get(User, int(current_user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify password
    if not verify_password(disable_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )
    
    # Verify TOTP code
    if not verify_totp_token(user.totp_secret, disable_data.totp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code"
        )
    
    # Disable 2FA
    user.is_2fa_enabled = False
    user.totp_secret = None
    user.backup_codes = None
    await db.commit()
    
    return MessageResponse(message="2FA disabled successfully")

# Helper functions
async def log_audit_event(
    db: AsyncSession,
    user_id: int,
    action: str,
    resource: str,
    resource_id: str,
    ip_address: str,
    description: str
):
    """Log audit event."""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        ip_address=ip_address,
        description=description
    )
    db.add(audit_log)
    await db.commit()

async def log_security_event(
    db: AsyncSession,
    event_type: str,
    severity: str,
    ip_address: str,
    description: str,
    user_id: int = None
):
    """Log security event."""
    security_event = SecurityEvent(
        event_type=event_type,
        severity=severity,
        ip_address=ip_address,
        description=description,
        user_id=user_id
    )
    db.add(security_event)
    await db.commit()

# Import the dependency function
from app.core.security import get_current_user_token

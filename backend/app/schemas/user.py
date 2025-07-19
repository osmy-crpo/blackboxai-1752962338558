from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from .common import AuditInfo

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    language: str = Field(default="en", regex="^(en|fr|ar)$")
    timezone: str = Field(default="UTC", max_length=50)
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    role_ids: Optional[List[int]] = []
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    language: Optional[str] = Field(None, regex="^(en|fr|ar)$")
    timezone: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = None
    role_ids: Optional[List[int]] = None

class UserLogin(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., min_length=1)
    remember_me: bool = False
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6)

class UserResponse(UserBase):
    id: int
    is_verified: bool
    is_superuser: bool
    is_2fa_enabled: bool
    avatar_url: Optional[str]
    last_login: Optional[datetime]
    password_changed_at: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    roles: List['RoleResponse'] = []
    
    class Config:
        from_attributes = True

class UserProfile(BaseModel):
    id: int
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    phone: Optional[str]
    avatar_url: Optional[str]
    language: str
    timezone: str
    is_2fa_enabled: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChangePassword(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class ResetPassword(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    scopes: List[str] = []

class RefreshToken(BaseModel):
    refresh_token: str

# 2FA Schemas
class Enable2FA(BaseModel):
    password: str
    
class Verify2FA(BaseModel):
    totp_code: str = Field(..., min_length=6, max_length=6)
    
class Setup2FAResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: List[str]

class Disable2FA(BaseModel):
    password: str
    totp_code: str = Field(..., min_length=6, max_length=6)

# Role and Permission Schemas
class PermissionBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    resource: str = Field(..., max_length=50)
    action: str = Field(..., max_length=50)

class PermissionResponse(PermissionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = []

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    permission_ids: Optional[List[int]] = None

class RoleResponse(RoleBase):
    id: int
    is_system_role: bool
    created_at: datetime
    updated_at: Optional[datetime]
    permissions: List[PermissionResponse] = []
    
    class Config:
        from_attributes = True

class UserRoleAssignment(BaseModel):
    user_id: int
    role_id: int
    expires_at: Optional[datetime] = None

# API Key Schemas
class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    scopes: Optional[List[str]] = []

class APIKeyResponse(BaseModel):
    id: int
    name: str
    key: str  # Only returned on creation
    description: Optional[str]
    expires_at: Optional[datetime]
    is_active: bool
    last_used: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Update forward references
UserResponse.model_rebuild()

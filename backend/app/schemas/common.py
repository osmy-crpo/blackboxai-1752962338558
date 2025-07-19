from pydantic import BaseModel, Field
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: Optional[str] = Field(default="asc", regex="^(asc|desc)$", description="Sort order")
    search: Optional[str] = Field(default=None, description="Search query")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool

class MessageResponse(BaseModel):
    message: str
    success: bool = True
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    message: str
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Any] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    database: bool
    redis: Optional[bool] = None

class FilterParams(BaseModel):
    is_active: Optional[bool] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None

class BulkOperationResponse(BaseModel):
    success_count: int
    error_count: int
    total_count: int
    errors: Optional[List[dict]] = None
    message: str

class ExportParams(BaseModel):
    format: str = Field(default="csv", regex="^(csv|xlsx|pdf)$")
    include_headers: bool = True
    date_format: str = Field(default="%Y-%m-%d %H:%M:%S")
    filters: Optional[dict] = None

class ImportParams(BaseModel):
    file_type: str = Field(regex="^(csv|xlsx)$")
    has_headers: bool = True
    skip_errors: bool = False
    update_existing: bool = False

class AuditInfo(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

class LocationInfo(BaseModel):
    zone: Optional[str] = None
    aisle: Optional[str] = None
    shelf: Optional[str] = None
    bin: Optional[str] = None

class AddressInfo(BaseModel):
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str

class ContactInfo(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    mobile: Optional[str] = None
    fax: Optional[str] = None

class GeoLocation(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

class FileUploadResponse(BaseModel):
    filename: str
    file_size: int
    file_type: str
    upload_url: str
    success: bool = True

class ValidationError(BaseModel):
    field: str
    message: str
    value: Any

class BulkValidationResponse(BaseModel):
    valid_items: List[dict]
    invalid_items: List[dict]
    validation_errors: List[ValidationError]
    summary: dict

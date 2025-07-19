from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class SupplierStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BLACKLISTED = "blacklisted"

class SupplierRating(str, enum.Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"
    UNRATED = "unrated"

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    legal_name = Column(String(255), nullable=True)
    
    # Contact information
    contact_person = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    mobile = Column(String(20), nullable=True)
    fax = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Address information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Business information
    tax_id = Column(String(50), nullable=True)
    registration_number = Column(String(100), nullable=True)
    business_type = Column(String(50), nullable=True)  # corporation, partnership, sole_proprietorship
    industry = Column(String(100), nullable=True)
    
    # Financial information
    credit_limit = Column(Numeric(12, 2), nullable=True)
    current_balance = Column(Numeric(12, 2), default=0.00)
    payment_terms = Column(String(100), nullable=True)  # Net 30, Net 60, COD, etc.
    currency = Column(String(3), default="USD")
    
    # Banking information
    bank_name = Column(String(255), nullable=True)
    bank_account = Column(String(100), nullable=True)
    bank_routing = Column(String(50), nullable=True)
    swift_code = Column(String(20), nullable=True)
    
    # Supplier performance
    status = Column(Enum(SupplierStatus), default=SupplierStatus.ACTIVE)
    rating = Column(Enum(SupplierRating), default=SupplierRating.UNRATED)
    lead_time_days = Column(Integer, nullable=True)
    minimum_order_amount = Column(Numeric(10, 2), nullable=True)
    
    # Performance metrics
    total_orders = Column(Integer, default=0)
    total_amount = Column(Numeric(15, 2), default=0.00)
    on_time_delivery_rate = Column(Numeric(5, 2), nullable=True)  # Percentage
    quality_rating = Column(Numeric(3, 2), nullable=True)  # 1-5 scale
    last_order_date = Column(DateTime(timezone=True), nullable=True)
    
    # Contract information
    contract_start_date = Column(DateTime(timezone=True), nullable=True)
    contract_end_date = Column(DateTime(timezone=True), nullable=True)
    contract_terms = Column(Text, nullable=True)
    
    # Additional information
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON string of tags
    
    # Certifications and compliance
    certifications = Column(Text, nullable=True)  # JSON string
    compliance_status = Column(String(50), nullable=True)
    last_audit_date = Column(DateTime(timezone=True), nullable=True)
    next_audit_date = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    products = relationship("Product", back_populates="supplier")
    supplier_products = relationship("SupplierProduct", back_populates="supplier")
    orders = relationship("Order", back_populates="supplier")
    contacts = relationship("SupplierContact", back_populates="supplier")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', code='{self.code}')>"

class SupplierProduct(Base):
    __tablename__ = "supplier_products"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Supplier-specific product information
    supplier_sku = Column(String(100), nullable=True)
    supplier_name = Column(String(255), nullable=True)  # Supplier's name for the product
    supplier_description = Column(Text, nullable=True)
    
    # Pricing information
    cost_price = Column(Numeric(10, 4), nullable=False)
    currency = Column(String(3), default="USD")
    price_valid_from = Column(DateTime(timezone=True), nullable=True)
    price_valid_to = Column(DateTime(timezone=True), nullable=True)
    
    # Order information
    minimum_order_quantity = Column(Integer, default=1)
    maximum_order_quantity = Column(Integer, nullable=True)
    lead_time_days = Column(Integer, nullable=True)
    
    # Package information
    package_size = Column(Integer, default=1)
    package_unit = Column(String(20), nullable=True)  # box, case, pallet, etc.
    weight_per_unit = Column(Numeric(8, 3), nullable=True)
    
    # Availability
    is_active = Column(Boolean, default=True)
    is_preferred = Column(Boolean, default=False)
    availability_status = Column(String(50), default="available")
    
    # Quality and performance
    quality_rating = Column(Numeric(3, 2), nullable=True)  # 1-5 scale
    last_order_date = Column(DateTime(timezone=True), nullable=True)
    total_ordered = Column(Integer, default=0)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="supplier_products")
    product = relationship("Product", back_populates="supplier_products")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<SupplierProduct(id={self.id}, supplier_id={self.supplier_id}, product_id={self.product_id})>"

class SupplierContact(Base):
    __tablename__ = "supplier_contacts"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    
    # Contact information
    name = Column(String(255), nullable=False)
    title = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    mobile = Column(String(20), nullable=True)
    
    # Contact type and preferences
    contact_type = Column(String(50), nullable=True)  # primary, billing, technical, sales
    is_primary = Column(Boolean, default=False)
    preferred_contact_method = Column(String(20), nullable=True)  # email, phone, mobile
    
    # Additional information
    notes = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    supplier = relationship("Supplier", back_populates="contacts")
    creator = relationship("User")
    
    def __repr__(self):
        return f"<SupplierContact(id={self.id}, name='{self.name}', supplier_id={self.supplier_id})>"

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Address information
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=False)
    
    # Geographic coordinates
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    
    # Contact information
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    manager_name = Column(String(255), nullable=True)
    
    # Warehouse specifications
    total_area = Column(Numeric(10, 2), nullable=True)  # in square meters
    storage_capacity = Column(Integer, nullable=True)   # number of items
    temperature_controlled = Column(Boolean, default=False)
    security_level = Column(String(20), default="standard")  # standard, high, maximum
    
    # Operating hours
    operating_hours = Column(Text, nullable=True)  # JSON string with daily hours
    timezone = Column(String(50), default="UTC")
    
    # Status
    is_active = Column(Boolean, default=True)
    is_main_warehouse = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    staff_assignments = relationship("WarehouseStaff", back_populates="warehouse")
    inventory_records = relationship("Inventory", back_populates="warehouse")
    inventory_movements = relationship("InventoryMovement", back_populates="warehouse")
    outbound_transfers = relationship("StockTransfer", foreign_keys="StockTransfer.from_warehouse_id", back_populates="from_warehouse")
    inbound_transfers = relationship("StockTransfer", foreign_keys="StockTransfer.to_warehouse_id", back_populates="to_warehouse")
    orders = relationship("Order", back_populates="warehouse")
    
    def __repr__(self):
        return f"<Warehouse(id={self.id}, name='{self.name}', code='{self.code}')>"

class WarehouseStaff(Base):
    __tablename__ = "warehouse_staff"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    
    # Assignment details
    position = Column(String(100), nullable=True)  # Manager, Supervisor, Worker, etc.
    department = Column(String(100), nullable=True)  # Receiving, Shipping, Inventory, etc.
    shift = Column(String(20), nullable=True)  # morning, afternoon, night
    
    # Permissions within warehouse
    can_receive_stock = Column(Boolean, default=True)
    can_ship_stock = Column(Boolean, default=True)
    can_adjust_inventory = Column(Boolean, default=False)
    can_manage_transfers = Column(Boolean, default=False)
    can_view_reports = Column(Boolean, default=False)
    
    # Employment details
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    is_primary_assignment = Column(Boolean, default=True)
    
    # Contact during work
    work_phone = Column(String(20), nullable=True)
    work_email = Column(String(255), nullable=True)
    emergency_contact = Column(String(255), nullable=True)
    
    # Performance tracking
    last_activity = Column(DateTime(timezone=True), nullable=True)
    total_transactions = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="warehouse_assignments")
    warehouse = relationship("Warehouse", back_populates="staff_assignments")
    assigner = relationship("User", foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f"<WarehouseStaff(id={self.id}, user_id={self.user_id}, warehouse_id={self.warehouse_id})>"

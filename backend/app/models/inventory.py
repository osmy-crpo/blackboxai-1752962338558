from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class MovementType(str, enum.Enum):
    STOCK_IN = "stock_in"
    STOCK_OUT = "stock_out"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    ADJUSTMENT_POSITIVE = "adjustment_positive"
    ADJUSTMENT_NEGATIVE = "adjustment_negative"
    RETURN_IN = "return_in"
    RETURN_OUT = "return_out"
    DAMAGED = "damaged"
    EXPIRED = "expired"
    LOST = "lost"
    FOUND = "found"

class TransferStatus(str, enum.Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    
    # Stock levels
    quantity_on_hand = Column(Integer, default=0, nullable=False)
    quantity_reserved = Column(Integer, default=0, nullable=False)  # Reserved for orders
    quantity_available = Column(Integer, default=0, nullable=False)  # On hand - reserved
    quantity_incoming = Column(Integer, default=0, nullable=False)  # Expected from transfers/orders
    
    # Location within warehouse
    location_zone = Column(String(50), nullable=True)  # A, B, C zones
    location_aisle = Column(String(20), nullable=True)  # A1, A2, etc.
    location_shelf = Column(String(20), nullable=True)  # 1, 2, 3, etc.
    location_bin = Column(String(20), nullable=True)   # A, B, C bins
    
    # Cost tracking (for FIFO/LIFO/Average cost)
    average_cost = Column(Numeric(10, 4), default=0.0000)
    last_cost = Column(Numeric(10, 4), default=0.0000)
    
    # Stock alerts
    low_stock_threshold = Column(Integer, nullable=True)
    reorder_point = Column(Integer, nullable=True)
    max_stock_level = Column(Integer, nullable=True)
    
    # Last activity
    last_movement_date = Column(DateTime(timezone=True), nullable=True)
    last_counted_date = Column(DateTime(timezone=True), nullable=True)
    last_counted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="inventory_records")
    warehouse = relationship("Warehouse", back_populates="inventory_records")
    movements = relationship("InventoryMovement", back_populates="inventory")
    counter = relationship("User", foreign_keys=[last_counted_by])
    
    def __repr__(self):
        return f"<Inventory(id={self.id}, product_id={self.product_id}, warehouse_id={self.warehouse_id}, qty={self.quantity_on_hand})>"

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    inventory_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    
    # Movement details
    movement_type = Column(Enum(MovementType), nullable=False)
    quantity = Column(Integer, nullable=False)  # Positive for in, negative for out
    unit_cost = Column(Numeric(10, 4), nullable=True)
    total_cost = Column(Numeric(12, 4), nullable=True)
    
    # Reference information
    reference_type = Column(String(50), nullable=True)  # order, transfer, adjustment, etc.
    reference_id = Column(Integer, nullable=True)
    reference_number = Column(String(100), nullable=True)
    
    # Before and after quantities
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    
    # Movement reason and notes
    reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Location information
    from_location = Column(String(100), nullable=True)
    to_location = Column(String(100), nullable=True)
    
    # Batch/Lot tracking
    batch_number = Column(String(100), nullable=True)
    lot_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # User who performed the movement
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    movement_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    inventory = relationship("Inventory", back_populates="movements")
    product = relationship("Product", back_populates="inventory_movements")
    warehouse = relationship("Warehouse", back_populates="inventory_movements")
    performer = relationship("User", foreign_keys=[performed_by])
    approver = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f"<InventoryMovement(id={self.id}, type={self.movement_type}, qty={self.quantity})>"

class StockTransfer(Base):
    __tablename__ = "stock_transfers"

    id = Column(Integer, primary_key=True, index=True)
    transfer_number = Column(String(100), unique=True, nullable=False, index=True)
    
    # Transfer details
    from_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    to_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    status = Column(Enum(TransferStatus), default=TransferStatus.PENDING)
    
    # Transfer information
    total_items = Column(Integer, default=0)
    total_quantity = Column(Integer, default=0)
    estimated_cost = Column(Numeric(12, 2), nullable=True)
    actual_cost = Column(Numeric(12, 2), nullable=True)
    
    # Dates
    requested_date = Column(DateTime(timezone=True), server_default=func.now())
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    shipped_date = Column(DateTime(timezone=True), nullable=True)
    received_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    
    # Personnel
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    shipped_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    received_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Shipping information
    carrier = Column(String(100), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    shipping_cost = Column(Numeric(10, 2), nullable=True)
    
    # Notes and reasons
    reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Priority
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    from_warehouse = relationship("Warehouse", foreign_keys=[from_warehouse_id], back_populates="outbound_transfers")
    to_warehouse = relationship("Warehouse", foreign_keys=[to_warehouse_id], back_populates="inbound_transfers")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    shipper = relationship("User", foreign_keys=[shipped_by])
    receiver = relationship("User", foreign_keys=[received_by])
    items = relationship("StockTransferItem", back_populates="transfer")
    
    def __repr__(self):
        return f"<StockTransfer(id={self.id}, number='{self.transfer_number}', status={self.status})>"

class StockTransferItem(Base):
    __tablename__ = "stock_transfer_items"

    id = Column(Integer, primary_key=True, index=True)
    transfer_id = Column(Integer, ForeignKey("stock_transfers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Quantities
    requested_quantity = Column(Integer, nullable=False)
    shipped_quantity = Column(Integer, default=0)
    received_quantity = Column(Integer, default=0)
    damaged_quantity = Column(Integer, default=0)
    
    # Cost information
    unit_cost = Column(Numeric(10, 4), nullable=True)
    total_cost = Column(Numeric(12, 4), nullable=True)
    
    # Batch/Lot information
    batch_number = Column(String(100), nullable=True)
    lot_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    damage_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    transfer = relationship("StockTransfer", back_populates="items")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<StockTransferItem(id={self.id}, transfer_id={self.transfer_id}, product_id={self.product_id})>"

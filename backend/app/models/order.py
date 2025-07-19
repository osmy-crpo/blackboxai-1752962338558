from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class OrderType(str, enum.Enum):
    CUSTOMER = "customer"      # Customer order (sale)
    INTERNAL = "internal"      # Internal transfer/requisition
    PURCHASE = "purchase"      # Purchase order from supplier
    RETURN = "return"          # Return order

class OrderStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    PICKING = "picking"
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REFUNDED = "refunded"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    REFUNDED = "refunded"
    FAILED = "failed"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(100), unique=True, nullable=False, index=True)
    order_type = Column(Enum(OrderType), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.DRAFT)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Warehouse assignment
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    
    # Customer information (for customer orders)
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)
    
    # Supplier information (for purchase orders)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    
    # Billing address
    billing_address_line1 = Column(String(255), nullable=True)
    billing_address_line2 = Column(String(255), nullable=True)
    billing_city = Column(String(100), nullable=True)
    billing_state = Column(String(100), nullable=True)
    billing_postal_code = Column(String(20), nullable=True)
    billing_country = Column(String(100), nullable=True)
    
    # Shipping address
    shipping_address_line1 = Column(String(255), nullable=True)
    shipping_address_line2 = Column(String(255), nullable=True)
    shipping_city = Column(String(100), nullable=True)
    shipping_state = Column(String(100), nullable=True)
    shipping_postal_code = Column(String(20), nullable=True)
    shipping_country = Column(String(100), nullable=True)
    
    # Financial information
    subtotal = Column(Numeric(12, 2), default=0.00)
    tax_amount = Column(Numeric(12, 2), default=0.00)
    shipping_cost = Column(Numeric(10, 2), default=0.00)
    discount_amount = Column(Numeric(10, 2), default=0.00)
    total_amount = Column(Numeric(12, 2), default=0.00)
    
    # Discount information
    discount_code = Column(String(50), nullable=True)
    discount_percentage = Column(Numeric(5, 2), nullable=True)
    
    # Shipping information
    shipping_method = Column(String(100), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    carrier = Column(String(100), nullable=True)
    estimated_delivery = Column(DateTime(timezone=True), nullable=True)
    actual_delivery = Column(DateTime(timezone=True), nullable=True)
    
    # Order dates
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    required_date = Column(DateTime(timezone=True), nullable=True)
    shipped_date = Column(DateTime(timezone=True), nullable=True)
    delivered_date = Column(DateTime(timezone=True), nullable=True)
    
    # Internal information
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    source = Column(String(50), nullable=True)  # web, mobile, phone, email, etc.
    sales_rep = Column(String(255), nullable=True)
    
    # Notes and special instructions
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    special_instructions = Column(Text, nullable=True)
    
    # Processing information
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    packed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    shipped_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    warehouse = relationship("Warehouse", back_populates="orders")
    supplier = relationship("Supplier", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    assignee = relationship("User", foreign_keys=[assigned_to])
    processor = relationship("User", foreign_keys=[processed_by])
    packer = relationship("User", foreign_keys=[packed_by])
    shipper = relationship("User", foreign_keys=[shipped_by])
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Order(id={self.id}, number='{self.order_number}', type={self.order_type}, status={self.status})>"

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    # Quantity information
    quantity_ordered = Column(Integer, nullable=False)
    quantity_shipped = Column(Integer, default=0)
    quantity_delivered = Column(Integer, default=0)
    quantity_returned = Column(Integer, default=0)
    
    # Pricing information
    unit_price = Column(Numeric(10, 4), nullable=False)
    discount_percentage = Column(Numeric(5, 2), default=0.00)
    discount_amount = Column(Numeric(10, 4), default=0.0000)
    line_total = Column(Numeric(12, 4), nullable=False)
    
    # Product information at time of order
    product_name = Column(String(255), nullable=False)  # Snapshot
    product_sku = Column(String(100), nullable=False)   # Snapshot
    product_description = Column(Text, nullable=True)   # Snapshot
    
    # Batch/Lot tracking
    batch_number = Column(String(100), nullable=True)
    lot_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # Special instructions for this item
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    
    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id}, qty={self.quantity_ordered})>"

class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Status change information
    from_status = Column(Enum(OrderStatus), nullable=True)
    to_status = Column(Enum(OrderStatus), nullable=False)
    
    # Change details
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    change_reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamp
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order")
    changer = relationship("User")
    
    def __repr__(self):
        return f"<OrderStatusHistory(id={self.id}, order_id={self.order_id}, from={self.from_status}, to={self.to_status})>"

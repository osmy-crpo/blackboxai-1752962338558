from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# Association table for many-to-many relationship between products and categories
product_categories = Table(
    'product_categories',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True)
)

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    barcode = Column(String(100), unique=True, nullable=True, index=True)
    
    # Pricing
    cost_price = Column(Numeric(10, 2), nullable=True)
    selling_price = Column(Numeric(10, 2), nullable=False)
    wholesale_price = Column(Numeric(10, 2), nullable=True)
    
    # Physical properties
    weight = Column(Numeric(8, 3), nullable=True)  # in kg
    dimensions_length = Column(Numeric(8, 2), nullable=True)  # in cm
    dimensions_width = Column(Numeric(8, 2), nullable=True)   # in cm
    dimensions_height = Column(Numeric(8, 2), nullable=True)  # in cm
    
    # Inventory settings
    track_inventory = Column(Boolean, default=True)
    min_stock_level = Column(Integer, default=0)
    max_stock_level = Column(Integer, nullable=True)
    reorder_point = Column(Integer, default=0)
    reorder_quantity = Column(Integer, default=0)
    
    # Product status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_digital = Column(Boolean, default=False)
    requires_shipping = Column(Boolean, default=True)
    
    # SEO and metadata
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON string of tags
    
    # Images and media
    image_url = Column(String(500), nullable=True)
    gallery_images = Column(Text, nullable=True)  # JSON string of image URLs
    
    # Supplier information
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    supplier_sku = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    categories = relationship("Category", secondary=product_categories, back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    inventory_records = relationship("Inventory", back_populates="product")
    inventory_movements = relationship("InventoryMovement", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    supplier_products = relationship("SupplierProduct", back_populates="product")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>"

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    
    # Hierarchy support
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    level = Column(Integer, default=0)
    sort_order = Column(Integer, default=0)
    
    # Category settings
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # SEO and metadata
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    products = relationship("Product", secondary=product_categories, back_populates="categories")
    parent = relationship("Category", remote_side=[id], backref="children")
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', slug='{self.slug}')>"

class ProductCategory(Base):
    __tablename__ = "product_category_assignments"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    is_primary = Column(Boolean, default=False)  # One primary category per product
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    product = relationship("Product")
    category = relationship("Category")
    assigner = relationship("User")
    
    def __repr__(self):
        return f"<ProductCategory(product_id={self.product_id}, category_id={self.category_id})>"

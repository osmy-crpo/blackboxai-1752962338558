from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    roles,
    products,
    categories,
    warehouses,
    inventory,
    orders,
    suppliers,
    notifications,
    analytics,
    reports
)

api_router = APIRouter()

# Authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# User management routes
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(roles.router, prefix="/roles", tags=["Roles & Permissions"])

# Product management routes
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])

# Warehouse management routes
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["Warehouses"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])

# Order management routes
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])

# Supplier management routes
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"])

# Notification routes
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])

# Analytics and reporting routes
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])

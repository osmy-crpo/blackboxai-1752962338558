# Warehouse Management System - Backend API

A comprehensive FastAPI-based backend for warehouse and sales management with multilingual support, security features, and modular architecture.

## 🚀 Features

### ✅ Authentication & Security
- JWT-based authentication with refresh tokens
- 2FA support with TOTP
- IP whitelisting and rate limiting
- Password hashing with bcrypt
- Audit logging for all operations
- Security event tracking

### ✅ Core Modules
- **Users & Roles**: RBAC system with permissions
- **Products & Categories**: Product management with SKU/barcode support
- **Warehouses**: Multi-warehouse support with staff assignments
- **Inventory**: Real-time stock tracking with movement logs
- **Orders**: Customer, internal, purchase, and return orders
- **Suppliers**: Supplier management with product relationships
- **Notifications**: Multi-channel notification system
- **Analytics**: Dashboard KPIs and reporting
- **Audit**: Complete audit trail and security monitoring

### ✅ Technical Features
- Async/await with SQLAlchemy 2.0
- PostgreSQL database with proper relationships
- Pydantic schemas for validation
- Swagger/OpenAPI documentation
- Modular service layer architecture
- Comprehensive error handling
- Pagination and filtering
- Search functionality

## 📋 Requirements

- Python 3.9+
- PostgreSQL 12+
- Redis (optional, for caching)

## 🛠️ Installation

1. **Clone and setup**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Database setup**:
```bash
# Create PostgreSQL database
createdb warehouse_db

# Or using psql
psql -c "CREATE DATABASE warehouse_db;"
```

3. **Environment configuration**:
```bash
cp .env.example .env
# Edit .env with your database credentials and settings
```

4. **Run the application**:
```bash
python run.py
```

The API will be available at:
- **API**: http://localhost:8001
- **Documentation**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 📚 API Documentation

### Authentication Endpoints
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/change-password` - Change password
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password with token

### 2FA Endpoints
- `POST /api/v1/auth/2fa/setup` - Setup 2FA
- `POST /api/v1/auth/2fa/verify` - Verify and enable 2FA
- `POST /api/v1/auth/2fa/disable` - Disable 2FA

### Core Resource Endpoints
- `GET/POST /api/v1/users` - User management
- `GET/POST /api/v1/roles` - Role and permission management
- `GET/POST /api/v1/products` - Product management
- `GET/POST /api/v1/categories` - Category management
- `GET/POST /api/v1/warehouses` - Warehouse management
- `GET/POST /api/v1/inventory` - Inventory tracking
- `GET/POST /api/v1/orders` - Order management
- `GET/POST /api/v1/suppliers` - Supplier management
- `GET/POST /api/v1/notifications` - Notification system

### Analytics & Reporting
- `GET /api/v1/analytics/dashboard` - Dashboard KPIs
- `GET /api/v1/analytics/sales` - Sales analytics
- `GET /api/v1/analytics/inventory` - Inventory analytics
- `GET /api/v1/reports/inventory` - Generate inventory reports
- `GET /api/v1/reports/sales` - Generate sales reports

## 🏗️ Architecture

### Project Structure
```
backend/
├── app/
│   ├── api/v1/endpoints/     # API route handlers
│   ├── core/                 # Core configuration and security
│   ├── models/              # SQLAlchemy database models
│   ├── schemas/             # Pydantic schemas for validation
│   ├── services/            # Business logic layer
│   └── main.py              # FastAPI application setup
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── run.py                  # Development server launcher
```

### Database Models
- **User**: User accounts with 2FA support
- **Role/Permission**: RBAC system
- **Product/Category**: Product catalog
- **Warehouse**: Multi-warehouse support
- **Inventory**: Stock tracking with movements
- **Order**: Order management system
- **Supplier**: Supplier relationships
- **Notification**: Multi-channel notifications
- **AuditLog**: Complete audit trail

### Security Features
- JWT tokens with configurable expiration
- Password complexity requirements
- Account lockout after failed attempts
- IP whitelisting support
- Rate limiting per endpoint
- Audit logging for sensitive operations
- Security event monitoring

## 🔧 Configuration

Key environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/warehouse_db

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENABLE_IP_WHITELIST=false

# Features
ENABLE_2FA=true
ENABLE_WEBSOCKET=true
DEFAULT_LANGUAGE=en
```

## 🧪 Testing

Run the development server and visit:
- http://localhost:8001/docs for interactive API documentation
- Test authentication endpoints
- Explore the complete API structure

## 📝 Next Steps (Phase 2)

1. **Frontend Development**: Build Next.js frontend with Tailwind CSS
2. **API Integration**: Connect frontend to backend APIs
3. **UI Implementation**: Create admin and warehouse staff interfaces
4. **Advanced Features**: Add real-time notifications, file uploads
5. **Production Deployment**: Docker containers and deployment setup

## 🔒 Security Notes

- Change default SECRET_KEY in production
- Enable IP whitelisting for production environments
- Configure proper CORS settings
- Set up SSL/TLS certificates
- Regular security audits and updates

## 📞 Support

This is Phase 1 of the Warehouse Management System. The backend API is fully functional with:
- ✅ Complete database models
- ✅ Authentication and security
- ✅ All core API endpoints
- ✅ Swagger documentation
- ✅ Modular architecture
- ✅ Error handling and validation

Ready for Phase 2: Frontend development!

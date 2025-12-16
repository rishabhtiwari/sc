# Auth Service

Multi-tenant authentication and user management microservice for the News Automation System.

## Overview

The Auth Service provides:
- **Authentication**: JWT-based login/logout with token verification
- **User Management**: CRUD operations for users with role-based access control
- **Customer Management**: Multi-tenant customer account management
- **Role Management**: System and custom role management with granular permissions
- **Audit Logging**: Comprehensive audit trail for all user actions

## Architecture

```
Client → API Server (validates JWT) → Auth Service
                ↓
         MongoDB (news database)
```

## Features

### 1. Authentication
- JWT token-based authentication (HS256 algorithm)
- 24-hour token expiration (configurable)
- Account lockout after 5 failed login attempts (30-minute lockout)
- Password hashing with bcrypt (12 rounds)

### 2. Multi-Tenancy
- Customer isolation at database level
- All queries filtered by `customer_id`
- Super admin can manage all customers
- Customer admins can only manage their own customer

### 3. Role-Based Access Control (RBAC)
- 5 system roles: Super Admin, Customer Admin, Editor, Publisher, Viewer
- 29 granular permissions across 7 categories
- Support for custom customer-specific roles
- Permission-based decorators for endpoint protection

### 4. Audit Logging
- Automatic logging of all write operations
- Tracks before/after states for updates
- Includes IP address and user agent
- Filterable by user, action, resource type, date range

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/verify` - Verify JWT token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - Logout (client-side token invalidation)
- `GET /api/auth/health` - Health check

### Customer Management (Super Admin Only)
- `POST /api/customers` - Create customer
- `GET /api/customers` - List customers
- `GET /api/customers/:id` - Get customer details
- `PUT /api/customers/:id` - Update customer
- `DELETE /api/customers/:id` - Delete customer (soft delete)

### User Management
- `POST /api/users` - Create user (requires `user.create` permission)
- `GET /api/users` - List users (requires `user.view` permission)
- `GET /api/users/:id` - Get user details (requires `user.view` permission)
- `PUT /api/users/:id` - Update user (requires `user.edit` permission)
- `DELETE /api/users/:id` - Delete user (requires `user.delete` permission)
- `POST /api/users/:id/reset-password` - Reset password (requires `user.edit` permission)
- `POST /api/users/:id/suspend` - Suspend user (Customer Admin only)
- `POST /api/users/:id/activate` - Activate user (Customer Admin only)

### Role Management
- `GET /api/roles` - List roles (system + customer-specific)
- `GET /api/roles/:id` - Get role details
- `POST /api/roles` - Create custom role (Customer Admin only)
- `PUT /api/roles/:id` - Update custom role (Customer Admin only)
- `DELETE /api/roles/:id` - Delete custom role (Customer Admin only)
- `GET /api/permissions` - Get all available permissions

### Audit Logs
- `GET /api/audit-logs` - List audit logs (requires `audit.view` permission)
- `GET /api/audit-logs/:id` - Get audit log details (requires `audit.view` permission)

## Default Credentials

**Super Admin:**
- Email: `admin@newsautomation.com`
- Password: `admin123`
- Customer: `customer_default`
- Role: Super Admin (all permissions)

## Environment Variables

```bash
# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=8098
FLASK_DEBUG=false
FLASK_ENV=production

# MongoDB Configuration
MONGODB_HOST=ichat-mongodb
MONGODB_PORT=27017
MONGODB_DATABASE=news
MONGODB_USERNAME=ichat_app
MONGODB_PASSWORD=ichat_app_password_2024

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-2024
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Password Configuration
BCRYPT_ROUNDS=12
MIN_PASSWORD_LENGTH=8

# Account Lockout Configuration
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/auth-service.log
```

## Running the Service

### With Docker Compose
```bash
docker-compose up auth-service
```

### Standalone
```bash
cd jobs/auth-service
python app.py
```

## Testing

### Login
```bash
curl -X POST http://localhost:8098/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@newsautomation.com",
    "password": "admin123"
  }'
```

### Verify Token
```bash
curl -X POST http://localhost:8098/api/auth/verify \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_JWT_TOKEN"
  }'
```

### Get Current User
```bash
curl -X GET http://localhost:8098/api/auth/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Permissions

### Categories
1. **news**: News article management
2. **video**: Video generation and management
3. **youtube**: YouTube upload management
4. **user**: User management
5. **settings**: System settings
6. **customer**: Customer management (Super Admin only)
7. **audit**: Audit log viewing

### Permission Keys
- `news.create`, `news.view`, `news.edit`, `news.delete`, `news.publish`
- `video.create`, `video.view`, `video.edit`, `video.delete`, `video.publish`
- `youtube.create`, `youtube.view`, `youtube.edit`, `youtube.delete`, `youtube.upload`
- `user.create`, `user.view`, `user.edit`, `user.delete`, `user.manage_roles`
- `settings.view`, `settings.edit`, `settings.manage_integrations`
- `customer.create`, `customer.view`, `customer.edit`, `customer.delete`
- `audit.view`, `audit.export`

## System Roles

### 1. Super Admin
- All 31 permissions
- Can manage all customers
- Can create/delete customers
- Full system access

### 2. Customer Admin
- All permissions except customer management
- Can manage users within their customer
- Can create custom roles
- Can view audit logs

### 3. Editor (Default Role)
- Content creation and editing
- Video generation
- YouTube upload management
- Cannot manage users or settings

### 4. Publisher
- Limited publishing permissions
- Can view and publish content
- Cannot create or edit content

### 5. Viewer
- Read-only access
- Can view news, videos, and YouTube uploads
- Cannot create, edit, or delete

## Database Collections

### customers
- `customer_id`: Unique customer identifier
- `company_name`: Company name
- `slug`: URL-friendly identifier
- `status`: trial, active, suspended, cancelled
- `subscription`: Plan details and billing info
- `limits`: Usage limits (users, videos, storage)

### users
- `user_id`: Unique user identifier
- `customer_id`: Associated customer
- `email`: User email (unique per customer)
- `password_hash`: Bcrypt hashed password
- `role_id`: Assigned role
- `status`: active, suspended, inactive
- `failed_login_attempts`: Failed login counter
- `account_locked_until`: Lockout expiration

### roles
- `role_id`: Unique role identifier
- `customer_id`: Associated customer (null for system roles)
- `role_name`: Display name
- `slug`: URL-friendly identifier
- `permissions`: Array of permission keys
- `is_system_role`: System vs custom role flag

### permissions
- `permission_key`: Unique permission identifier
- `permission_name`: Display name
- `category`: Permission category
- `description`: Permission description

### audit_logs
- `log_id`: Unique log identifier
- `customer_id`: Associated customer
- `user_id`: User who performed action
- `action`: create, read, update, delete
- `resource_type`: Type of resource affected
- `resource_id`: ID of affected resource
- `changes`: Before/after state
- `metadata`: IP address, user agent, etc.
- `timestamp`: Action timestamp

## Security Considerations

1. **Change JWT Secret**: Update `JWT_SECRET_KEY` in production
2. **Change Default Password**: Reset super admin password after first login
3. **Enable HTTPS**: Use HTTPS in production
4. **Rate Limiting**: Consider adding rate limiting for login endpoint
5. **Token Refresh**: Implement token refresh mechanism for long sessions
6. **Password Policy**: Enforce stronger password requirements
7. **MFA**: Consider adding multi-factor authentication

## Future Enhancements

- [ ] Email verification for new users
- [ ] Password reset via email
- [ ] Multi-factor authentication (MFA)
- [ ] OAuth2 integration (Google, GitHub, etc.)
- [ ] Token refresh mechanism
- [ ] Rate limiting for API endpoints
- [ ] IP whitelisting for customers
- [ ] Session management
- [ ] Password history tracking
- [ ] Custom password policies per customer


# Customer Onboarding & User Management Workflow

## Table of Contents
1. [Customer Onboarding Flow](#customer-onboarding-flow)
2. [User Management](#user-management)
3. [Role & Permission Management](#role--permission-management)
4. [UI Screens & Components](#ui-screens--components)
5. [API Endpoints](#api-endpoints)
6. [Database Schema](#database-schema)

---

## 1. Customer Onboarding Flow

### 1.1 Super Admin Creates New Customer

**Actor**: Super Admin (role_super_admin)

**Steps**:
1. Super Admin logs into the system
2. Navigates to **Admin Panel** → **Customers**
3. Clicks **"Add New Customer"** button
4. Fills in customer registration form:
   - Customer Name (required)
   - Company Name
   - Contact Email (required)
   - Contact Phone
   - Address
   - Subscription Plan (Free/Basic/Pro/Enterprise)
   - Status (Active/Inactive/Suspended)
   - Notes

5. System generates:
   - `customer_id`: Unique identifier (e.g., `customer_abc123`)
   - `created_at`: Timestamp
   - `is_active`: true

6. Super Admin clicks **"Create Customer"**
7. System creates customer record in `customers` collection

**API Call**:
```http
POST /api/auth/customers
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "name": "Acme News Corp",
  "company_name": "Acme Corporation",
  "contact_email": "admin@acmenews.com",
  "contact_phone": "+1-555-0123",
  "address": "123 News Street, NY 10001",
  "subscription_plan": "pro",
  "status": "active"
}
```

**Response**:
```json
{
  "success": true,
  "customer": {
    "customer_id": "customer_abc123",
    "name": "Acme News Corp",
    "company_name": "Acme Corporation",
    "contact_email": "admin@acmenews.com",
    "subscription_plan": "pro",
    "status": "active",
    "created_at": "2025-12-16T10:30:00Z"
  }
}
```

---

### 1.2 Super Admin Creates Customer Admin User

**Steps**:
1. After customer creation, Super Admin navigates to **Users** tab
2. Clicks **"Create Customer Admin"** button
3. Fills in user form:
   - Email (required) - e.g., `admin@acmenews.com`
   - First Name (required)
   - Last Name (required)
   - Password (required, min 8 chars)
   - Customer: Select from dropdown (pre-selected if coming from customer page)
   - Role: **Customer Admin** (role_customer_admin)
   - Status: Active

4. System generates:
   - `user_id`: Unique identifier (e.g., `user_xyz789`)
   - Password hash using bcrypt
   - Links user to customer via `customer_id`

5. System sends welcome email to customer admin with:
   - Login credentials
   - Portal URL
   - Getting started guide

**API Call**:
```http
POST /api/auth/users
Authorization: Bearer <super_admin_token>
Content-Type: application/json

{
  "email": "admin@acmenews.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "customer_id": "customer_abc123",
  "role_id": "role_customer_admin",
  "is_active": true
}
```

---

### 1.3 Customer Admin First Login

**Steps**:
1. Customer Admin receives welcome email
2. Opens portal URL: `https://newsautomation.com/login`
3. Enters credentials:
   - Email: `admin@acmenews.com`
   - Password: `SecurePass123!`

4. System validates credentials and generates JWT token with:
   ```json
   {
     "user_id": "user_xyz789",
     "customer_id": "customer_abc123",
     "email": "admin@acmenews.com",
     "role_id": "role_customer_admin",
     "permissions": [
       "news.view", "news.create", "news.update", "news.delete",
       "video.view", "video.create", "video.update", "video.delete",
       "user.view", "user.create", "user.update", "user.delete",
       "config.view", "config.update",
       "dashboard.view", "analytics.view"
     ]
   }
   ```

5. Customer Admin is redirected to **Dashboard**
6. System shows **"Complete Your Profile"** wizard (optional):
   - Upload company logo
   - Configure news sources
   - Set up YouTube credentials
   - Configure video settings

---

## 2. User Management

### 2.1 Customer Admin Creates New User

**Actor**: Customer Admin

**Steps**:
1. Customer Admin logs in
2. Navigates to **Settings** → **User Management**
3. Sees list of existing users in their organization
4. Clicks **"Add New User"** button
5. Fills in user creation form:
   - Email (required)
   - First Name (required)
   - Last Name (required)
   - Password (required)
   - Role: Select from dropdown
     - **Editor** (role_editor) - Can create/edit news and videos
     - **Viewer** (role_viewer) - Read-only access
     - **Operator** (role_operator) - Can manage operations but not users
   - Status: Active/Inactive

6. System automatically sets `customer_id` from logged-in user's context
7. Clicks **"Create User"**
8. System creates user and sends welcome email

**UI Screen**: User Management Page

```
┌─────────────────────────────────────────────────────────────┐
│  User Management                                    [+ Add User] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Search: [____________]  Role: [All ▼]  Status: [All ▼]     │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Name          Email              Role      Status  Actions│
│  ├───────────────────────────────────────────────────────┤  │
│  │ John Doe      admin@acme.com    Admin     Active   [⋮] │
│  │ Jane Smith    jane@acme.com     Editor    Active   [⋮] │
│  │ Bob Johnson   bob@acme.com      Viewer    Inactive [⋮] │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  Showing 3 of 3 users                    [< 1 2 3 >]        │
└─────────────────────────────────────────────────────────────┘
```

**API Call**:
```http
POST /api/auth/users
Authorization: Bearer <customer_admin_token>
X-Customer-ID: customer_abc123
X-User-ID: user_xyz789
Content-Type: application/json

{
  "email": "jane@acmenews.com",
  "password": "TempPass456!",
  "first_name": "Jane",
  "last_name": "Smith",
  "role_id": "role_editor"
}
```

---

### 2.2 View Users List

**API Call**:
```http
GET /api/auth/users?page=1&page_size=20&role_id=role_editor&status=active
Authorization: Bearer <customer_admin_token>
X-Customer-ID: customer_abc123
```

**Response**:
```json
{
  "success": true,
  "users": [
    {
      "user_id": "user_xyz789",
      "email": "admin@acmenews.com",
      "first_name": "John",
      "last_name": "Doe",
      "role_id": "role_customer_admin",
      "role_name": "Customer Admin",
      "is_active": true,
      "last_login_at": "2025-12-16T09:00:00Z",
      "created_at": "2025-12-01T10:00:00Z"
    },
    {
      "user_id": "user_abc456",
      "email": "jane@acmenews.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "role_id": "role_editor",
      "role_name": "Editor",
      "is_active": true,
      "last_login_at": "2025-12-16T08:30:00Z",
      "created_at": "2025-12-10T14:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 2,
    "total_pages": 1
  }
}
```

---

### 2.3 Update User

**Steps**:
1. Customer Admin clicks **[⋮]** menu next to user
2. Selects **"Edit User"**
3. Modal opens with user details
4. Can update:
   - First Name / Last Name
   - Role (if has permission)
   - Status (Active/Inactive)
   - Reset Password

**API Call**:
```http
PUT /api/auth/users/user_abc456
Authorization: Bearer <customer_admin_token>
X-Customer-ID: customer_abc123
X-User-ID: user_xyz789
Content-Type: application/json

{
  "first_name": "Jane",
  "last_name": "Smith-Johnson",
  "role_id": "role_operator",
  "is_active": true
}
```

---

### 2.4 Delete/Deactivate User

**Steps**:

### 3.3 Create Custom Role (Future Enhancement)

**Actor**: Customer Admin or Super Admin

**Steps**:
1. Navigate to **Settings** → **Roles & Permissions**
2. Click **"Create Custom Role"**
3. Fill in role details:
   - Role Name (required)
   - Description
   - Select permissions from categorized list

4. System generates `role_id` and creates role

**UI Screen**: Create Role Modal

```
┌─────────────────────────────────────────────────────────────┐
│  Create Custom Role                                    [×]   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Role Name: [_____________________________]                  │
│                                                               │
│  Description:                                                 │
│  [___________________________________________]                │
│  [___________________________________________]                │
│                                                               │
│  Select Permissions:                                          │
│                                                               │
│  ▼ News Management                                           │
│    ☑ news.view      - View news articles                    │
│    ☑ news.create    - Create news articles                  │
│    ☐ news.update    - Update news articles                  │
│    ☐ news.delete    - Delete news articles                  │
│                                                               │
│  ▼ Video Management                                          │
│    ☑ video.view     - View videos                           │
│    ☐ video.create   - Generate videos                       │
│    ☐ video.update   - Update videos                         │
│    ☐ video.delete   - Delete videos                         │
│                                                               │
│  ▶ User Management                                           │
│  ▶ Configuration Management                                  │
│  ▶ Dashboard & Analytics                                     │
│  ▶ YouTube Management                                        │
│                                                               │
│                                    [Cancel]  [Create Role]   │
└─────────────────────────────────────────────────────────────┘
```

**API Call**:
```http
POST /api/auth/roles
Authorization: Bearer <customer_admin_token>
X-Customer-ID: customer_abc123
Content-Type: application/json

{
  "name": "Content Creator",
  "description": "Can create and view content but not delete",
  "permissions": [
    "news.view",
    "news.create",
    "video.view",
    "video.create",
    "dashboard.view"
  ]
}
```

---

### 3.4 Assign Role to User

**Steps**:
1. Navigate to **User Management**
2. Click **[⋮]** menu next to user
3. Select **"Change Role"**
4. Select new role from dropdown
5. Click **"Update"**

**API Call**:
```http
PUT /api/auth/users/user_abc456
Authorization: Bearer <customer_admin_token>
X-Customer-ID: customer_abc123
Content-Type: application/json

{
  "role_id": "role_editor"
}
```

---

## 4. UI Screens & Components

### 4.1 Login Screen

```
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│                    📰 News Automation                         │
│                                                               │
│                        Login                                  │
│                                                               │
│  Email:                                                       │
│  [_____________________________]                              │
│                                                               │
│  Password:                                                    │
│  [_____________________________]  [👁]                        │
│                                                               │
│  ☐ Remember me                                               │
│                                                               │
│                    [Login]                                    │
│                                                               │
│  Forgot password?                                            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**API Call**:
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@acmenews.com",
  "password": "SecurePass123!"
}
```

**Response**:
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "user_id": "user_xyz789",
    "email": "admin@acmenews.com",
    "first_name": "John",
    "last_name": "Doe",
    "customer_id": "customer_abc123",
    "role_id": "role_customer_admin",
    "permissions": ["news.view", "news.create", ...]
  }
}
```

---

### 4.2 Dashboard (After Login)

```
┌─────────────────────────────────────────────────────────────┐
│  📰 News Automation          John Doe (Admin) [▼] [🔔] [⚙]  │
├─────────────────────────────────────────────────────────────┤
│  Dashboard  News  Videos  Analytics  Settings               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Overview                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │   247    │ │   165    │ │   142    │ │    12    │       │
│  │  Total   │ │  Videos  │ │ Uploaded │ │Processing│       │
│  │  News    │ │ Generated│ │to YouTube│ │          │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                               │
│  Recent Activity                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 📰 News fetch completed - 23 articles (5 min ago)     │  │
│  │ 🎤 Audio generation in progress - 18 articles (8 min) │  │
│  │ 🎬 Video generation completed - 15 videos (15 min)    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  Workflow Status                                              │
│  News Fetch ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 98%      │
│  Audio Gen  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 92%      │
│  Video Gen  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 97%      │
│  Upload     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 99%      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Note**: All data shown is filtered by `customer_id` from JWT token.

---

### 4.3 User Management Screen

```
┌─────────────────────────────────────────────────────────────┐
│  Settings → User Management                    [+ Add User]  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Search: [____________]  Role: [All ▼]  Status: [All ▼]     │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Name          Email              Role      Status  Actions│
│  ├───────────────────────────────────────────────────────┤  │
│  │ John Doe      admin@acme.com    Admin     ● Active  [⋮] │
│  │ Jane Smith    jane@acme.com     Editor    ● Active  [⋮] │
│  │ Bob Johnson   bob@acme.com      Viewer    ○ Inactive[⋮] │
│  │ Alice Brown   alice@acme.com    Operator  ● Active  [⋮] │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  Showing 4 of 4 users                    [< 1 >]            │
└─────────────────────────────────────────────────────────────┘
```

**Actions Menu [⋮]**:
- Edit User
- Change Role
- Reset Password
- Deactivate User
- Delete User
- View Activity Log

---

### 4.4 Add User Modal

```
┌─────────────────────────────────────────────────────────────┐
│  Add New User                                          [×]   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Email: *                                                     │
│  [_____________________________]                              │
│                                                               │
│  First Name: *                                                │
│  [_____________________________]                              │
│                                                               │
│  Last Name: *                                                 │
│  [_____________________________]                              │
│                                                               │
│  Password: *                                                  │
│  [_____________________________]  [Generate]                  │
│  Password strength: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│                                                               │
│  Role: *                                                      │
│  [Customer Admin ▼]                                          │
│    - Customer Admin (Full access)                            │
│    - Editor (Create/edit content)                            │
│    - Operator (Manage operations)                            │
│    - Viewer (Read-only)                                      │
│                                                               │
│  ☑ Send welcome email                                        │
│  ☑ User must change password on first login                 │
│                                                               │
│                                    [Cancel]  [Create User]   │
└─────────────────────────────────────────────────────────────┘
```

---

### 4.5 Roles & Permissions Screen

```
┌─────────────────────────────────────────────────────────────┐
│  Settings → Roles & Permissions                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┬───────────────────────────────────────┐    │
│  │ Roles       │ Role Details                          │    │
│  ├─────────────┼───────────────────────────────────────┤    │
│  │             │                                       │    │
│  │ ▶ Super     │ Customer Admin                        │    │
│  │   Admin     │ Full access within customer org       │    │
│  │             │                                       │    │
│  │ ▼ Customer  │ Users with this role: 2               │    │
│  │   Admin     │                                       │    │
│  │             │ Permissions (24):                     │    │
│  │ ▶ Editor    │                                       │    │
│  │             │ News Management                       │    │
│  │ ▶ Operator  │   ☑ news.view                        │    │
│  │             │   ☑ news.create                      │    │
│  │ ▶ Viewer    │   ☑ news.update                      │    │
│  │             │   ☑ news.delete                      │    │
│  │             │                                       │    │
│  │             │ Video Management                      │    │
│  │             │   ☑ video.view                       │    │
│  │             │   ☑ video.create                     │    │
│  │             │   ☑ video.update                     │    │
│  │             │   ☑ video.delete                     │    │
│  │             │                                       │    │
│  │             │ User Management                       │    │
│  │             │   ☑ user.view                        │    │
│  │             │   ☑ user.create                      │    │
│  │             │   ☑ user.update                      │    │
│  │             │   ☑ user.delete                      │    │
│  │             │                                       │    │
│  │             │ ... (more permissions)                │    │
│  │             │                                       │    │
│  └─────────────┴───────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. API Endpoints

### 5.1 Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/login` | User login | No |
| POST | `/api/auth/logout` | User logout | Yes |
| POST | `/api/auth/verify` | Verify JWT token | Yes |
| POST | `/api/auth/refresh` | Refresh JWT token | Yes |
| POST | `/api/auth/forgot-password` | Request password reset | No |
| POST | `/api/auth/reset-password` | Reset password with token | No |

---

### 5.2 Customer Management Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|---------------------|
| GET | `/api/auth/customers` | List all customers | `customer.view` (Super Admin) |
| POST | `/api/auth/customers` | Create customer | `customer.create` (Super Admin) |
| GET | `/api/auth/customers/:id` | Get customer details | `customer.view` |
| PUT | `/api/auth/customers/:id` | Update customer | `customer.update` |
| DELETE | `/api/auth/customers/:id` | Delete customer | `customer.delete` (Super Admin) |

---

### 5.3 User Management Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|---------------------|
| GET | `/api/auth/users` | List users (filtered by customer) | `user.view` |
| POST | `/api/auth/users` | Create user | `user.create` |
| GET | `/api/auth/users/:id` | Get user details | `user.view` |
| PUT | `/api/auth/users/:id` | Update user | `user.update` |
| DELETE | `/api/auth/users/:id` | Delete user | `user.delete` |
| POST | `/api/auth/users/:id/reset-password` | Reset user password | `user.update` |
| POST | `/api/auth/users/:id/deactivate` | Deactivate user | `user.update` |

---

### 5.4 Role & Permission Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|---------------------|
| GET | `/api/auth/roles` | List all roles | `role.view` |
| POST | `/api/auth/roles` | Create custom role | `role.create` |
| GET | `/api/auth/roles/:id` | Get role details | `role.view` |
| PUT | `/api/auth/roles/:id` | Update role | `role.update` |
| DELETE | `/api/auth/roles/:id` | Delete role | `role.delete` |
| GET | `/api/auth/permissions` | List all permissions | `role.view` |

---

### 5.5 Audit Log Endpoints

| Method | Endpoint | Description | Permission Required |
|--------|----------|-------------|---------------------|
| GET | `/api/auth/audit-logs` | List audit logs (filtered by customer) | `audit.view` |
| GET | `/api/auth/audit-logs/:id` | Get audit log details | `audit.view` |

---

## 6. Database Schema

### 6.1 Customers Collection

```javascript
{
  customer_id: "customer_abc123",           // Unique identifier
  name: "Acme News Corp",                   // Customer name
  company_name: "Acme Corporation",         // Company name
  contact_email: "admin@acmenews.com",      // Primary contact
  contact_phone: "+1-555-0123",             // Phone number
  address: "123 News Street, NY 10001",     // Address
  subscription_plan: "pro",                 // free/basic/pro/enterprise
  status: "active",                         // active/inactive/suspended
  settings: {                               // Customer-specific settings
    max_users: 10,
    max_news_per_day: 100,
    features_enabled: ["video", "audio", "youtube"]
  },
  created_at: ISODate("2025-12-01T10:00:00Z"),
  updated_at: ISODate("2025-12-16T10:00:00Z"),
  is_deleted: false
}
```

**Indexes**:
- `customer_id` (unique)
- `contact_email` (unique)
- `status`

---

### 6.2 Users Collection

```javascript
{
  user_id: "user_xyz789",                   // Unique identifier
  customer_id: "customer_abc123",           // Customer reference
  email: "admin@acmenews.com",              // Email (unique per customer)
  password_hash: "$2b$12$...",              // Bcrypt hash
  first_name: "John",
  last_name: "Doe",
  role_id: "role_customer_admin",           // Role reference
  is_active: true,                          // Active status
  email_verified: true,
  phone: "+1-555-0456",
  avatar_url: null,
  last_login_at: ISODate("2025-12-16T09:00:00Z"),
  failed_login_attempts: 0,
  locked_until: null,
  password_changed_at: ISODate("2025-12-01T10:00:00Z"),
  must_change_password: false,
  created_at: ISODate("2025-12-01T10:00:00Z"),
  updated_at: ISODate("2025-12-16T10:00:00Z"),
  created_by: "user_super_admin",
  updated_by: "user_xyz789",
  is_deleted: false
}
```

**Indexes**:
- `user_id` (unique)
- `customer_id` + `email` (unique compound)
- `customer_id` + `is_deleted`
- `role_id`

---

### 6.3 Roles Collection

```javascript
{
  role_id: "role_customer_admin",           // Unique identifier
  name: "Customer Admin",                   // Display name
  description: "Full access within customer organization",
  is_system_role: true,                     // Cannot be deleted
  permissions: [                            // Array of permission codes
    "news.view",
    "news.create",
    "news.update",
    "news.delete",
    "video.view",
    "video.create",
    "user.view",
    "user.create",
    "user.update",
    "user.delete",
    "config.view",
    "config.update",
    "dashboard.view",
    "analytics.view"
  ],
  created_at: ISODate("2025-12-01T00:00:00Z"),
  updated_at: ISODate("2025-12-01T00:00:00Z"),
  is_deleted: false
}
```

**Indexes**:
- `role_id` (unique)
- `is_system_role`

---

### 6.4 Permissions Collection

```javascript
{
  permission_id: "perm_news_view",          // Unique identifier
  code: "news.view",                        // Permission code
  name: "View News",                        // Display name
  description: "View news articles",        // Description
  category: "news",                         // Category for grouping
  created_at: ISODate("2025-12-01T00:00:00Z"),
  is_deleted: false
}
```

**Indexes**:
- `permission_id` (unique)
- `code` (unique)
- `category`

---

### 6.5 Audit Logs Collection

```javascript
{
  log_id: "log_abc123",                     // Unique identifier
  customer_id: "customer_abc123",           // Customer reference
  user_id: "user_xyz789",                   // User who performed action
  action: "create",                         // create/read/update/delete/login/logout
  resource_type: "user",                    // Type of resource
  resource_id: "user_abc456",               // Resource identifier
  changes: {                                // What changed
    before: { role_id: "role_viewer" },
    after: { role_id: "role_editor" }
  },
  metadata: {                               // Additional context
    ip_address: "192.168.1.100",
    user_agent: "Mozilla/5.0...",
    request_id: "req_xyz"
  },
  status: "success",                        // success/failure
  error_message: null,
  timestamp: ISODate("2025-12-16T10:30:00Z")
}
```

**Indexes**:
- `log_id` (unique)
- `customer_id` + `timestamp` (compound, descending)
- `user_id` + `timestamp` (compound, descending)
- `resource_type` + `resource_id`
- `action`

---

## 7. Complete Workflow Example

### Scenario: Acme News Corp Onboarding

**Step 1: Super Admin Creates Customer**
```
Super Admin → Admin Panel → Customers → Add New Customer
  ↓
Creates "Acme News Corp" with Pro plan
  ↓
System generates customer_id: "customer_acme_001"
```

**Step 2: Super Admin Creates Customer Admin**
```
Super Admin → Users → Create User
  ↓
Email: admin@acmenews.com
Role: Customer Admin
Customer: Acme News Corp
  ↓
System sends welcome email with credentials
```

**Step 3: Customer Admin First Login**
```
admin@acmenews.com → Login
  ↓
JWT token generated with customer_id and permissions
  ↓
Redirected to Dashboard (sees only Acme News Corp data)
```

**Step 4: Customer Admin Creates Editor**
```
Customer Admin → Settings → User Management → Add User
  ↓
Email: editor@acmenews.com
Role: Editor
  ↓
System creates user linked to customer_acme_001
  ↓
Editor receives welcome email
```

**Step 5: Editor Logs In and Creates News**
```
editor@acmenews.com → Login
  ↓
JWT token with editor permissions
  ↓
Dashboard → News → Create News Article
  ↓
System saves with customer_id: "customer_acme_001"
  ↓
Only Acme News Corp users can see this article
```

**Step 6: Customer Admin Views Audit Logs**
```
Customer Admin → Settings → Audit Logs
  ↓
Sees all actions by Acme News Corp users:
  - admin@acmenews.com created user editor@acmenews.com
  - editor@acmenews.com created news article "Breaking News"
  - editor@acmenews.com generated video for article
```

---

## 8. Security Considerations

### 8.1 Multi-Tenant Data Isolation

✅ **All API endpoints extract `customer_id` from JWT token**
✅ **All database queries filter by `customer_id`**
✅ **Users cannot access data from other customers**
✅ **Super Admin can access all customers (for support)**

### 8.2 Permission Checks

✅ **Every protected endpoint checks permissions**
✅ **Frontend hides UI elements based on permissions**
✅ **Backend validates permissions on every request**

### 8.3 Audit Logging

✅ **All user actions are logged**
✅ **Logs include before/after state for updates**
✅ **Logs are immutable (no updates/deletes)**
✅ **Logs are filtered by customer_id**

---

## 9. Frontend Implementation Notes

### 9.1 React Components Needed

1. **Authentication**
   - `LoginPage.jsx`
   - `ForgotPasswordPage.jsx`
   - `ResetPasswordPage.jsx`

2. **User Management**
   - `UserListPage.jsx`
   - `UserCreateModal.jsx`
   - `UserEditModal.jsx`
   - `UserDeleteConfirmDialog.jsx`

3. **Role Management**
   - `RoleListPage.jsx`
   - `RoleDetailsPanel.jsx`
   - `RoleCreateModal.jsx`
   - `PermissionCheckbox.jsx`

4. **Audit Logs**
   - `AuditLogListPage.jsx`
   - `AuditLogDetailsModal.jsx`
   - `AuditLogFilters.jsx`

### 9.2 State Management

Use React Context or Redux to store:
- Current user info (from JWT)
- User permissions (for UI rendering)
- Customer info

### 9.3 API Client

Create axios interceptor to:
- Add `Authorization: Bearer <token>` header
- Add `X-Customer-ID` and `X-User-ID` headers
- Handle 401 (redirect to login)
- Handle 403 (show permission denied)

---

## 10. Testing Checklist

### 10.1 Multi-Tenancy Tests

- [ ] User from Customer A cannot see data from Customer B
- [ ] User from Customer A cannot create data for Customer B
- [ ] User from Customer A cannot update data from Customer B
- [ ] User from Customer A cannot delete data from Customer B
- [ ] Super Admin can see all customers' data

### 10.2 Permission Tests

- [ ] Viewer cannot create/update/delete
- [ ] Editor can create/update but not delete users
- [ ] Operator can manage operations but not users
- [ ] Customer Admin can do everything except manage other customers
- [ ] Super Admin can do everything

### 10.3 Audit Log Tests

- [ ] User creation is logged
- [ ] User update is logged with before/after
- [ ] User deletion is logged
- [ ] Login/logout is logged
- [ ] Failed login attempts are logged
- [ ] Audit logs are filtered by customer_id

---

## Summary

This workflow provides:

1. ✅ **Clear onboarding process** for new customers
2. ✅ **Self-service user management** for customer admins
3. ✅ **Role-based access control** with 5 default roles
4. ✅ **Permission-based UI rendering** for better UX
5. ✅ **Complete audit trail** for compliance
6. ✅ **Multi-tenant data isolation** for security
7. ✅ **Scalable architecture** for growth

All endpoints and UI screens respect the multi-tenant architecture with proper `customer_id` filtering at every level.

1. Customer Admin clicks **[⋮]** menu next to user
2. Selects **"Deactivate User"** or **"Delete User"**
3. Confirmation dialog appears
4. System performs soft delete (sets `is_deleted: true`) or deactivation (`is_active: false`)

**API Call**:
```http
DELETE /api/auth/users/user_abc456
Authorization: Bearer <customer_admin_token>
X-Customer-ID: customer_abc123
```

---

## 3. Role & Permission Management

### 3.1 Default Roles

The system comes with 5 pre-defined roles:

| Role ID | Role Name | Description | Permissions Count |
|---------|-----------|-------------|-------------------|
| `role_super_admin` | Super Admin | Full system access | All (29) |
| `role_customer_admin` | Customer Admin | Full access within customer | 24 |
| `role_editor` | Editor | Create/edit content | 16 |
| `role_operator` | Operator | Manage operations | 12 |
| `role_viewer` | Viewer | Read-only access | 5 |

---

### 3.2 View Roles & Permissions

**UI Screen**: Roles & Permissions Page

```
┌─────────────────────────────────────────────────────────────┐
│  Roles & Permissions                        [+ Create Role]  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Role: Customer Admin                                 │    │
│  │ Description: Full access within customer organization│    │
│  │                                                       │    │
│  │ Permissions (24):                                    │    │
│  │                                                       │    │
│  │ News Management                                      │    │
│  │   ☑ news.view      - View news articles             │    │
│  │   ☑ news.create    - Create news articles           │    │
│  │   ☑ news.update    - Update news articles           │    │
│  │   ☑ news.delete    - Delete news articles           │    │
│  │                                                       │    │
│  │ Video Management                                     │    │
│  │   ☑ video.view     - View videos                    │    │
│  │   ☑ video.create   - Generate videos                │    │
│  │   ☑ video.update   - Update videos                  │    │
│  │   ☑ video.delete   - Delete videos                  │    │
│  │                                                       │    │
│  │ User Management                                      │    │
│  │   ☑ user.view      - View users                     │    │
│  │   ☑ user.create    - Create users                   │    │
│  │   ☑ user.update    - Update users                   │    │
│  │   ☑ user.delete    - Delete users                   │    │
│  │                                                       │    │
│  │ ... (more permissions)                               │    │
│  │                                                       │    │
│  │                              [Edit Role] [Delete]    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

**API Call to Get Roles**:
```http
GET /api/auth/roles
Authorization: Bearer <customer_admin_token>
```

**Response**:
```json
{
  "success": true,
  "roles": [
    {
      "role_id": "role_customer_admin",
      "name": "Customer Admin",
      "description": "Full access within customer organization",
      "is_system_role": true,
      "permissions": [
        "news.view", "news.create", "news.update", "news.delete",
        "video.view", "video.create", "video.update", "video.delete",
        "user.view", "user.create", "user.update", "user.delete",
        "config.view", "config.update",
        "dashboard.view", "analytics.view"
      ],
      "created_at": "2025-12-01T00:00:00Z"
    }
  ]
}
```

---


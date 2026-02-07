# Instagram UI Implementation Status

## ✅ What's Already Implemented

### 1. Individual Instagram Account Management (User-Level)
**Location**: `/social-platform/instagram`

**Components**:
- ✅ `InstagramCredentialsManager.jsx` - Manages user's Instagram account connections
- ✅ `InstagramPlatformPage.jsx` - Dedicated page for Instagram platform

**Features**:
- ✅ Connect Instagram Business accounts via OAuth
- ✅ View list of connected Instagram accounts
- ✅ Display account status (Connected/Disconnected)
- ✅ Disconnect Instagram accounts
- ✅ Requirements info banner
- ✅ Setup instructions
- ✅ OAuth popup flow
- ✅ Auto-refresh after OAuth completion

**API Integration**:
- ✅ `GET /api/social-media/instagram/oauth/initiate` - Start OAuth flow
- ✅ `GET /api/social-media/instagram/oauth/callback` - Handle OAuth callback
- ✅ `GET /api/social-media/instagram/credentials` - List user's credentials
- ✅ `DELETE /api/social-media/instagram/credentials/:id` - Delete credential

**Route**: 
- ✅ `/social-platform/instagram` - Registered in `App.jsx`

---

## ❌ What's Missing - Master App Management (Admin-Level)

### 2. Master App Management UI (NOT IMPLEMENTED)
**Needed Location**: `/settings` (new tab) or `/social-platform/settings`

**Missing Components**:
- ❌ `MasterAppManager.jsx` - Main master app management component
- ❌ `MasterAppList.jsx` - List all master apps for customer
- ❌ `MasterAppForm.jsx` - Create/Edit master app form
- ❌ `MasterAppCard.jsx` - Display individual master app details

**Missing Features**:
- ❌ List all master apps (Instagram, TikTok, Twitter, etc.)
- ❌ Create new master app with platform selection
- ❌ Edit existing master app (app_id, app_secret, redirect_uri, scopes)
- ❌ Delete master app (with warning about affected users)
- ❌ Activate/Deactivate master app
- ❌ View which users are using each master app
- ❌ Platform selector (Instagram, TikTok, Twitter, LinkedIn, Facebook, Reddit)
- ❌ Encryption key auto-generation indicator
- ❌ Master app status indicators (Active/Inactive)

**Missing API Integration**:
- ❌ `POST /api/social-media/master-apps` - Create master app
- ❌ `GET /api/social-media/master-apps` - List master apps
- ❌ `GET /api/social-media/master-apps/:id` - Get master app
- ❌ `PUT /api/social-media/master-apps/:id` - Update master app
- ❌ `DELETE /api/social-media/master-apps/:id` - Delete master app
- ❌ `POST /api/social-media/master-apps/:id/activate` - Activate/deactivate

**Missing Routes**:
- ❌ No route for master app management page
- ❌ No navigation link in sidebar/settings

---

## 🔧 Required Changes

### 1. Update `SettingsPage.jsx`
Add a new tab for "Social Media Apps":

```jsx
const tabs = [
  { id: 'users', name: 'User Management', icon: <UserIcon />, permission: 'user.view' },
  { id: 'roles', name: 'Roles & Permissions', icon: <ShieldIcon />, permission: 'role.view' },
  { id: 'social-apps', name: 'Social Media Apps', icon: <AppsIcon />, permission: 'admin' }, // NEW
  { id: 'audit', name: 'Audit Logs', icon: <ClipboardIcon />, permission: 'audit.view' }
];
```

### 2. Update `InstagramCredentialsManager.jsx`
Add check for master app before allowing connections:

```jsx
const handleConnectInstagram = async () => {
  // Check if master app exists
  const masterAppsResponse = await api.get('/social-media/master-apps?platform=instagram&active_only=true');
  
  if (!masterAppsResponse.data.master_apps || masterAppsResponse.data.master_apps.length === 0) {
    showToast('No Instagram app configured. Please contact your administrator.', 'error');
    return;
  }
  
  // Continue with OAuth...
};
```

### 3. Update `InstagramPlatformPage.jsx`
Add banner if no master app is configured:

```jsx
{!hasMasterApp && (
  <Card className="bg-yellow-50 border-yellow-200">
    <div className="flex items-center gap-3">
      <span className="text-3xl">⚠️</span>
      <div>
        <h3 className="font-semibold text-yellow-900">Instagram App Not Configured</h3>
        <p className="text-yellow-700 text-sm">
          Your administrator needs to configure an Instagram app before you can connect accounts.
          {isAdmin && <Link to="/settings?tab=social-apps">Configure now</Link>}
        </p>
      </div>
    </div>
  </Card>
)}
```

---

## 📋 Implementation Checklist

### Phase 1: Master App Management UI (Admin)
- [ ] Create `MasterAppManager.jsx` component
- [ ] Create `MasterAppList.jsx` component
- [ ] Create `MasterAppForm.jsx` component (modal/wizard)
- [ ] Create `MasterAppCard.jsx` component
- [ ] Add "Social Media Apps" tab to `SettingsPage.jsx`
- [ ] Add route for master app management
- [ ] Implement API service methods in `socialMediaService.js`
- [ ] Add permission checks (admin only)

### Phase 2: Update Instagram User Flow
- [ ] Update `InstagramCredentialsManager.jsx` to check for master app
- [ ] Update `InstagramPlatformPage.jsx` to show master app status
- [ ] Add "No master app" warning banner
- [ ] Display which master app is being used
- [ ] Add link to settings for admins

### Phase 3: Testing
- [ ] Test master app CRUD operations
- [ ] Test user flow when no master app exists
- [ ] Test user flow with active master app
- [ ] Test multiple users connecting with same master app
- [ ] Test admin vs regular user permissions

---

## 🎨 UI Design Recommendations

### Master App Management Page
```
┌─────────────────────────────────────────────────────────┐
│ Social Media Apps                    [+ Add New App]    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│ │ 📸 Instagram │  │ 🎵 TikTok    │  │ 🐦 Twitter   │  │
│ │              │  │              │  │              │  │
│ │ Production   │  │ Not Config   │  │ Not Config   │  │
│ │ ✅ Active    │  │              │  │              │  │
│ │              │  │              │  │              │  │
│ │ 5 users      │  │ [Configure]  │  │ [Configure]  │  │
│ │ [Edit] [⋮]   │  │              │  │              │  │
│ └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Master App Form (Modal)
```
┌─────────────────────────────────────────────┐
│ Create Instagram Master App          [✕]   │
├─────────────────────────────────────────────┤
│                                             │
│ App Name: [Production Instagram App____]   │
│                                             │
│ Facebook App ID: [876162771907731______]   │
│                                             │
│ Facebook App Secret: [********************] │
│                                             │
│ Redirect URI:                               │
│ [http://localhost:8080/api/social-media/..] │
│                                             │
│ Scopes:                                     │
│ ☑ instagram_basic                           │
│ ☑ instagram_content_publish                 │
│ ☑ pages_read_engagement                     │
│                                             │
│ ☑ Set as active app                         │
│                                             │
│ ℹ️ Encryption key will be auto-generated    │
│                                             │
│           [Cancel]  [Create App]            │
└─────────────────────────────────────────────┘
```

---

## 🚀 Next Steps

1. **Create Master App Management UI** (Priority: HIGH)
   - Implement components listed above
   - Add to Settings page
   - Test CRUD operations

2. **Update User Flow** (Priority: MEDIUM)
   - Add master app checks
   - Show helpful error messages
   - Guide users to admin if no app configured

3. **Documentation** (Priority: LOW)
   - User guide for connecting Instagram
   - Admin guide for configuring master apps
   - Troubleshooting guide


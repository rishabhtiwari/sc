// Migration: Create linkedin_credentials collection
// Description: Store LinkedIn OAuth credentials in MongoDB for multi-account support
// Date: 2026-01-24

print('Running migration: 059_create_linkedin_credentials.js');

// Switch to news database
db = db.getSiblingDB('news');

// Create linkedin_credentials collection
db.createCollection('linkedin_credentials');
print('✓ Created linkedin_credentials collection');

// Create indexes
db.getCollection('linkedin_credentials').createIndex({ "credential_id": 1 }, { unique: true });
db.getCollection('linkedin_credentials').createIndex({ "customer_id": 1 });
db.getCollection('linkedin_credentials').createIndex({ "is_active": 1 });
db.getCollection('linkedin_credentials').createIndex({ "created_at": -1 });
db.getCollection('linkedin_credentials').createIndex({ "customer_id": 1, "is_active": 1 });
print('✓ Created indexes for linkedin_credentials collection');

// Schema structure for linkedin_credentials collection:
// {
//     "credential_id": "string (unique identifier, UUID)",
//     "name": "string (friendly name for this credential, e.g., 'Personal LinkedIn', 'Company Page')",
//     "platform": "string (always 'linkedin')",
//     
//     // OAuth 2.0 credentials
//     "client_id": "string (LinkedIn Client ID)",
//     "client_secret": "string (LinkedIn Client Secret)",
//     "access_token": "string (OAuth access token)",
//     "refresh_token": "string (OAuth refresh token, if available)",
//     "token_expiry": "Date (when the access token expires)",
//     "scopes": ["array of strings (OAuth scopes granted, e.g., 'w_member_social', 'r_liteprofile')"],
//     
//     // LinkedIn account information
//     "person_id": "string (LinkedIn person URN)",
//     "profile_id": "string (LinkedIn profile ID)",
//     "first_name": "string (LinkedIn first name)",
//     "last_name": "string (LinkedIn last name)",
//     "profile_picture_url": "string (LinkedIn profile picture URL)",
//     "email": "string (LinkedIn email address)",
//     
//     // Organization/Company Page (if applicable)
//     "organization_id": "string (LinkedIn organization URN, if posting as company)",
//     "organization_name": "string (Company/Organization name)",
//     "is_organization_admin": "boolean (whether user is admin of organization)",
//     
//     // Multi-tenancy fields
//     "customer_id": "string (customer ID for multi-tenancy)",
//     
//     // Status and metadata
//     "is_active": "boolean (whether this credential is currently active/default)",
//     "is_authenticated": "boolean (whether OAuth flow is complete)",
//     "last_used_at": "Date (last time this credential was used for posting)",
//     "last_token_refresh": "Date (last time token was refreshed)",
//     
//     // Audit fields
//     "created_at": "Date (when credential was created)",
//     "updated_at": "Date (when credential was last updated)",
//     "created_by": "string (user ID who created this credential)",
//     "updated_by": "string (user ID who last updated this credential)",
//     
//     // Additional metadata
//     "notes": "string (optional notes about this credential)",
//     "post_count": "number (total number of posts using this credential)",
//     "last_post_status": "string (status of last post: success, failed, pending)"
// }

print('✓ Migration 059_create_linkedin_credentials.js completed successfully');


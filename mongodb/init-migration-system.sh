#!/bin/bash

# MongoDB Migration System Initialization Script
# This script runs during container initialization and sets up the migration system

set -e

echo "=== MongoDB Migration System Initialization ==="

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to be ready..."
until mongosh --eval "print('MongoDB is ready')" > /dev/null 2>&1; do
    sleep 2
done

echo "MongoDB is ready. Setting up migration system..."

# Create application user with database permissions
mongosh <<EOF
use admin

// Create application user with read/write permissions for both databases
db.createUser({
  user: 'ichat_app',
  pwd: 'ichat_app_password_2024',
  roles: [
    {
      role: 'readWrite',
      db: 'ichat_db'
    },
    {
      role: 'readWrite',
      db: 'news'
    }
  ]
});

print('Application user created successfully');
EOF

echo "Running migrations..."

# Run the migration script
/app/scripts/run-migrations.sh

echo "=== MongoDB Migration System Setup Complete ==="

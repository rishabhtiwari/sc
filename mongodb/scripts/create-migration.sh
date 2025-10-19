#!/bin/bash

# MongoDB Migration Creator Script
# Usage: ./create-migration.sh "migration_description"

set -e

MIGRATIONS_DIR="$(dirname "$0")/../migrations"
SCRIPT_DIR="$(dirname "$0")"

# Check if description is provided
if [ -z "$1" ]; then
    echo "Usage: $0 \"migration_description\""
    echo "Example: $0 \"add_user_preferences_table\""
    exit 1
fi

DESCRIPTION="$1"
TIMESTAMP=$(date +%Y%m%d%H%M%S)

# Get the next migration number
LAST_MIGRATION=$(find "$MIGRATIONS_DIR" -name "*.js" -type f | sort | tail -1)
if [ -n "$LAST_MIGRATION" ]; then
    LAST_NUMBER=$(basename "$LAST_MIGRATION" | cut -d'_' -f1)
    NEXT_NUMBER=$(printf "%03d" $((10#$LAST_NUMBER + 1)))
else
    NEXT_NUMBER="001"
fi

# Create migration filename
MIGRATION_NAME="${NEXT_NUMBER}_${DESCRIPTION}.js"
MIGRATION_FILE="$MIGRATIONS_DIR/$MIGRATION_NAME"

# Create migration template
cat > "$MIGRATION_FILE" << EOF
// Migration: $MIGRATION_NAME
// Description: $DESCRIPTION
// Date: $(date +%Y-%m-%d)

print('Running migration: $MIGRATION_NAME');

// TODO: Add your migration code here
// Example:
// db.createCollection('new_collection');
// db.new_collection.createIndex({ "field": 1 });
// db.existing_collection.updateMany({}, { \$set: { new_field: "default_value" } });

print('Migration $MIGRATION_NAME completed successfully');
EOF

echo "Created new migration: $MIGRATION_FILE"
echo ""
echo "Migration template created with the following content:"
echo "----------------------------------------"
cat "$MIGRATION_FILE"
echo "----------------------------------------"
echo ""
echo "Edit the migration file to add your database changes, then rebuild the MongoDB container to apply it."
echo ""
echo "To test the migration locally:"
echo "  docker-compose build ichat-mongodb"
echo "  docker-compose up ichat-mongodb"

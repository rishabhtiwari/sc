#!/bin/bash

# MongoDB Migration Runner Script
# This script runs all pending migrations in order

set -e

MIGRATIONS_DIR="/app/migrations"
DB_NAME="ichat_db"
MONGO_AUTH="--authenticationDatabase admin -u ichat_admin -p ichat_secure_password_2024"

echo "=== Running MongoDB Migrations ==="

# Check if migrations directory exists
if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "Migrations directory not found: $MIGRATIONS_DIR"
    exit 1
fi

# Function to check if a migration has been executed
is_migration_executed() {
    local migration_id="$1"

    # Check if migration has been executed by counting records
    local output=$(mongosh $MONGO_AUTH $DB_NAME --eval "
        try {
            const count = db.getCollection('_migrations').countDocuments({migration_id: '$migration_id'});
            print('COUNT:' + count);
        } catch (e) {
            print('COUNT:0');
        }
    " 2>&1)

    local count=$(echo "$output" | grep "COUNT:" | cut -d: -f2 | tr -d '\r\n')

    if [ -n "$count" ] && [ "$count" -gt 0 ]; then
        echo "true"
    else
        echo "false"
    fi
}

# Function to mark migration as executed
mark_migration_executed() {
    local migration_id="$1"
    local migration_file="$2"

    echo "  → Marking migration $migration_id as executed..."

    # Insert migration record
    mongosh $MONGO_AUTH $DB_NAME --eval "
        try {
            // Ensure the collection exists
            if (!db.getCollectionNames().includes('_migrations')) {
                db.createCollection('_migrations');
                db.getCollection('_migrations').createIndex({ 'migration_id': 1 }, { unique: true });
                db.getCollection('_migrations').createIndex({ 'executed_at': 1 });
            }

            db.getCollection('_migrations').insertOne({
                migration_id: '$migration_id',
                migration_file: '$migration_file',
                executed_at: new Date(),
                status: 'completed'
            });
        } catch (e) {
            // Ignore duplicate key errors (migration already tracked)
        }
    " >/dev/null 2>&1

    echo "  ✓ Migration $migration_id marked as executed"
}

# Function to execute a migration
execute_migration() {
    local migration_file="$1"
    local migration_id=$(basename "$migration_file" .js)

    echo "Checking migration: $migration_id"

    local is_executed_output=$(is_migration_executed "$migration_id")
    local is_executed=$(echo "$is_executed_output" | tail -1)

    if [ "$is_executed" = "true" ]; then
        echo "  ✓ Migration $migration_id already executed, skipping"
        return 0
    fi

    echo "  → Executing migration: $migration_id"
    
    # Execute the migration
    if mongosh --quiet $MONGO_AUTH "$DB_NAME" < "$migration_file"; then
        mark_migration_executed "$migration_id" "$migration_file"
        echo "  ✓ Migration $migration_id completed successfully"
    else
        echo "  ✗ Migration $migration_id failed"
        # Mark as failed
        mongosh --quiet $MONGO_AUTH --eval "
            use $DB_NAME;
            try {
                // Ensure the collection exists
                if (!db.getCollectionNames().includes('_migrations')) {
                    db.createCollection('_migrations');
                    db.getCollection('_migrations').createIndex({ 'migration_id': 1 }, { unique: true });
                    db.getCollection('_migrations').createIndex({ 'executed_at': 1 });
                }

                db.getCollection('_migrations').insertOne({
                    migration_id: '$migration_id',
                    migration_file: '$migration_file',
                    executed_at: new Date(),
                    status: 'failed',
                    error: 'Migration execution failed'
                });
            } catch (e) {
                // Ignore tracking errors for failed migrations
            }
        " >/dev/null 2>&1
        exit 1
    fi
}

# Get all migration files sorted by name (which should include timestamp/version)
migration_files=$(find "$MIGRATIONS_DIR" -name "*.js" -type f | sort)

if [ -z "$migration_files" ]; then
    echo "No migration files found in $MIGRATIONS_DIR"
    exit 0
fi

echo "Found migrations:"
echo "$migration_files" | while read -r file; do
    echo "  - $(basename "$file")"
done

# Execute migrations in order
echo ""
echo "Executing migrations..."
while IFS= read -r migration_file; do
    execute_migration "$migration_file"
done <<< "$migration_files"

echo ""
echo "=== All migrations completed successfully ==="

# Show migration status
echo ""
echo "Migration history:"
mongosh --quiet $MONGO_AUTH --eval "
    use $DB_NAME;
    db._migrations.find().sort({executed_at: 1}).forEach(function(doc) {
        print('  ' + doc.migration_id + ' - ' + doc.status + ' - ' + doc.executed_at);
    });
"

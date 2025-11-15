# MongoDB with Migration System
FROM mongo:7.0

# Install required packages for migration system
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Create directories for migrations and scripts
RUN mkdir -p /docker-entrypoint-initdb.d \
    /app/migrations \
    /app/scripts \
    /var/log/mongodb

# Copy migration system scripts
COPY scripts/ /app/scripts/
COPY migrations/ /app/migrations/

# Make scripts executable
RUN chmod +x /app/scripts/*.sh

# Copy the initialization script that sets up the migration system (for fresh databases)
COPY init-migration-system.sh /docker-entrypoint-initdb.d/00-init-migration-system.sh
RUN chmod +x /docker-entrypoint-initdb.d/00-init-migration-system.sh

# Create a simple wrapper script that handles both fresh and existing databases
COPY mongodb-wrapper.sh /usr/local/bin/mongodb-wrapper.sh
RUN chmod +x /usr/local/bin/mongodb-wrapper.sh

# Set up log directory permissions
RUN chown -R mongodb:mongodb /var/log/mongodb

# Expose MongoDB port
EXPOSE 27017

# Use our wrapper script that handles both fresh and existing databases
ENTRYPOINT ["/usr/local/bin/mongodb-wrapper.sh"]
CMD ["mongod", "--auth", "--bind_ip_all", "--logpath", "/var/log/mongodb/mongod.log", "--logappend"]

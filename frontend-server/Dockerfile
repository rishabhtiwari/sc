# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install production dependencies only
RUN npm install --production

# Copy built files from builder
COPY --from=builder /app/dist ./dist
COPY server.js ./

# Create logs and data directories
RUN mkdir -p /app/logs /app/data

# Expose port
EXPOSE 3002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3002/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Create entrypoint script to fix permissions at runtime
RUN echo '#!/bin/sh\n\
mkdir -p /app/logs /app/data\n\
chmod 777 /app/logs /app/data\n\
exec node server.js' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Start server via entrypoint
ENTRYPOINT ["/entrypoint.sh"]


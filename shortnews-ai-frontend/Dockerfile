# Use Node.js 18 as base image
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install system dependencies for React Native and Expo
RUN apk add \
    git \
    bash \
    curl \
    python3 \
    make \
    g++ \
    && npm install -g @expo/cli

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose ports for Expo dev server
EXPOSE 3002 3003 8081 19000 19001 19002

# Default command to start Expo development server
CMD ["npx", "expo", "start", "--web", "--port", "8081", "--host", "lan"]

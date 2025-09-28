#!/bin/bash

# iChat Assistant - Compile and Run Script
# This script compiles the Java application and runs it with the enhanced client-side document storage

echo "🚀 iChat Assistant - Enhanced Client-Side Document Storage"
echo "=========================================================="

# Check if Java is installed
if ! command -v javac &> /dev/null; then
    echo "❌ Error: Java compiler (javac) not found. Please install Java JDK 11 or higher."
    exit 1
fi

if ! command -v java &> /dev/null; then
    echo "❌ Error: Java runtime (java) not found. Please install Java JRE 11 or higher."
    exit 1
fi

# Check Java version
JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1-2)
echo "☕ Java version: $JAVA_VERSION"

# Create output directory
echo "📁 Creating output directory..."
mkdir -p out/production/sc

# Compile Java sources
echo "🔨 Compiling Java sources..."

# Find all Java files
JAVA_FILES=$(find src -name "*.java" | tr '\n' ' ')

# Use JavaFX from the project's external library configuration
JAVAFX_PATH="../javafx-sdk-25/lib"

# Check if the JavaFX path exists
if [ ! -d "$JAVAFX_PATH" ]; then
    echo "❌ Error: JavaFX library not found at $JAVAFX_PATH"
    echo "💡 Please ensure JavaFX SDK is installed at the expected location"
    echo "   Current working directory: $(pwd)"
    echo "   Looking for JavaFX at: $(realpath $JAVAFX_PATH 2>/dev/null || echo $JAVAFX_PATH)"
    exit 1
fi

# Compile with JavaFX
echo "📦 Using JavaFX from: $JAVAFX_PATH"
echo "📦 Resolved path: $(realpath $JAVAFX_PATH)"

# Create classpath with all JavaFX JARs
JAVAFX_CLASSPATH=""
for jar in "$JAVAFX_PATH"/*.jar; do
    if [ -f "$jar" ]; then
        if [ -z "$JAVAFX_CLASSPATH" ]; then
            JAVAFX_CLASSPATH="$jar"
        else
            JAVAFX_CLASSPATH="$JAVAFX_CLASSPATH:$jar"
        fi
    fi
done

# Add JSON library to classpath
JSON_LIB="lib/json-20240303.jar"
if [ -f "$JSON_LIB" ]; then
    JAVAFX_CLASSPATH="$JAVAFX_CLASSPATH:$JSON_LIB"
    echo "📚 Added JSON library: $JSON_LIB"
else
    echo "⚠️  JSON library not found at: $JSON_LIB"
fi

echo "📚 Full Classpath: $JAVAFX_CLASSPATH"

# Compile with JavaFX and JSON library in classpath
javac -cp "src:$JAVAFX_CLASSPATH" -d out/production/sc $JAVA_FILES

# Check compilation result
if [ $? -eq 0 ]; then
    echo "✅ Compilation successful!"
else
    echo "❌ Compilation failed!"
    exit 1
fi

# Check if API server is running
echo "🔍 Checking API server status..."
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api/health 2>/dev/null || echo "000")

if [ "$API_HEALTH" = "200" ]; then
    echo "✅ API server is running and healthy"
else
    echo "⚠️  API server not detected. Starting services..."
    echo "💡 Make sure to run: ./start-services.sh"
    echo "   Or manually start the Docker services:"
    echo "   docker-compose up -d"
fi

# Run the application
echo "🎯 Starting iChat Assistant..."
echo "📍 Look for the purple 'iC' icon in your system tray/menu bar"
echo ""

# Run with JavaFX and JSON library in classpath
echo "🚀 Running with full classpath..."
java -cp "out/production/sc:$JAVAFX_CLASSPATH" Main

echo ""
echo "👋 iChat Assistant has been closed."
echo "🔧 If you encountered issues:"
echo "   1. Make sure Java 11+ is installed"
echo "   2. Install JavaFX: https://openjfx.io/"
echo "   3. Start the API server: ./start-services.sh"
echo "   4. Check the console output for error messages"

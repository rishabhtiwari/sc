FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Fix numpy and scipy versions to avoid compatibility issues
RUN pip install --no-cache-dir \
    numpy==1.24.3 \
    scipy==1.10.1

# Install Flask and dependencies
RUN pip install --no-cache-dir \
    Flask==3.0.0 \
    Werkzeug==3.0.1 \
    itsdangerous \
    click \
    Jinja2 \
    MarkupSafe

# Install other dependencies
RUN pip install --no-cache-dir \
    pymongo==4.6.0 \
    requests==2.31.0

# Install iopaint - it will use the already installed numpy/scipy
RUN pip install --no-cache-dir \
    iopaint[all]==1.5.3

# Copy common utilities
COPY common /app/common

# Copy service files
COPY watermark-remover/iopaint_ui_service.py /app/iopaint_ui_service.py

# Create output directory
RUN mkdir -p /app/output

# Expose port
EXPOSE 8096

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=120s \
    CMD curl -f http://localhost:8096/health || exit 1

# Start Flask UI Service with IOPaint and MongoDB integration
CMD python iopaint_ui_service.py


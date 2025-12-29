# Power Benchmarking Suite - Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
COPY requirements-observability.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-observability.txt

# Copy application code
COPY . .

# Install package
RUN pip install -e .

# Create non-root user
RUN useradd -m -s /bin/bash powerbench && \
    echo "powerbench ALL=(ALL) NOPASSWD: /usr/bin/powermetrics" >> /etc/sudoers

# Switch to non-root user
USER powerbench

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import power_benchmarking_suite; print('OK')" || exit 1

# Default command
CMD ["power-benchmark", "--help"]



# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy backend requirements first (for better caching)
COPY backend/requirements.txt ./

# Install system dependencies and Python packages
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy backend code
COPY backend/ ./

# Expose port
EXPOSE 10000

# Run the application
CMD ["python", "app.py"]

FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for OpenCV and Mediapipe
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libpulse0 \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt gunicorn==20.1.0 eventlet==0.33.3

# Copy the application code
COPY . .

# Make sure audio directory exists
RUN mkdir -p audio

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 8080

# Command to run when the container starts - simplified without worker threads
CMD exec gunicorn --bind :$PORT --worker-class eventlet --timeout 120 --workers 1 main:application
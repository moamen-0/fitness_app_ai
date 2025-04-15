FROM python:3.9-slim

WORKDIR /app

# Install dependencies for OpenCV and Mediapipe
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
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV MEDIAPIPE_MODEL_COMPLEXITY=1

# Expose the port
EXPOSE 8080

# Command to run when the container starts
CMD exec gunicorn --bind :$PORT --worker-class eventlet --workers 1 --threads 8 --timeout 0 "main:application"
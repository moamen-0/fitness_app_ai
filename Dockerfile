FROM python:3.10-slim

WORKDIR /app

# Install dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements_cloud.txt .
RUN pip install --no-cache-dir -r requirements_cloud.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run with WebSocket support
CMD exec gunicorn --bind :$PORT --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker app:app
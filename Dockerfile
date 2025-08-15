# Use Python 3.13.2 as base image
FROM python:3.13.2-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies including FFmpeg and uv
RUN apt-get update && apt-get install -y \
    gcc \
    ffmpeg \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Verify FFmpeg installation
RUN ffmpeg -version

# Copy project configuration files
COPY pyproject.toml .
COPY uv.lock* .

# Create virtual environment and install dependencies
RUN uv sync --frozen

# Copy application files
COPY discord_bot.py .

# Create startup script to ensure .env file exists
RUN echo '#!/bin/bash\n\
if [ ! -f .env ]; then\n\
    echo "Creating empty .env file..."\n\
    touch .env\n\
fi\n\
exec uv run discord_bot.py' > /app/start.sh && \
    chmod +x /app/start.sh

# Command to run the application using startup script
CMD ["/app/start.sh"] 
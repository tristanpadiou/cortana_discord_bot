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
COPY config_example.py .

# Create a non-root user to run the application
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port for Hugging Face spaces (typically 7860)
# EXPOSE 7860

# Health check - disabled for Discord bot as it doesn't expose HTTP endpoints
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD python -c "import sys; sys.exit(0)"

# Command to run the application using uv
CMD ["uv", "run", "discord_bot.py"] 
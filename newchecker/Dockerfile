# 🐔 HAMZZY FX BOT - Railway Optimized
# Uses Python 3.10-slim for minimal size
# Proper health checks to prevent Railway from killing the bot
# Cached layers for faster builds

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir \
    --upgrade pip \
    && pip install --no-cache-dir \
    pyTelegramBotAPI==4.18.0 \
    requests==2.31.0 \
    faker==20.1.0 \
    aiohttp==3.9.1 \
    aiofiles==23.2.1 \
    asyncio==3.4.3 \
    && apt-get purge -y --auto-remove gcc \
    && rm -rf /root/.cache/pip

# Copy the rest of the application
COPY . .

# Create Data directory
RUN mkdir -p Data

# Health check to keep Railway happy
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Expose port (Railway uses this)
EXPOSE 8080

# Run the bot
CMD ["python", "bot.py"]

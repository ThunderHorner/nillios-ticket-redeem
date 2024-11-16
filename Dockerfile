FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and curl
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Install Nillion CLI
RUN curl https://nilup.nilogy.xyz/install.sh | bash

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy necessary files and directories
COPY ticketing_system/nada_programs/target/ticket_check.nada.bin /app/ticketing_system/nada_programs/target/
COPY ticketing_system/ticket_check/*.py /app/ticketing_system/ticket_check/

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=ticketing_system.ticket_check.flask_app
ENV FLASK_ENV=production
ENV PATH="/root/.nillion/bin:${PATH}"

# Create and switch to non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Create entrypoint script directly in Dockerfile
RUN echo '#!/bin/bash\nnillion-devnet &\nsleep 5\npython -m flask run --host=0.0.0.0' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
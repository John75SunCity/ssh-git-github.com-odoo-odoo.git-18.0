# Use an official Python image as the base
FROM python:3.9-slim

# Switch to root user to install system dependencies
USER root

# Install required system dependencies
RUN apt-get update && apt-get install -y \
    python-dev \
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Switch back to the odoo user
USER odoo

# Set environment variables to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Ensure commands are run as root for apt-get
USER root

# Clean up apt directories and remove stale locks
RUN rm -rf /var/lib/apt/lists/* && mkdir -p /var/lib/apt/lists/partial
RUN rm -f /var/lib/dpkg/lock

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    ssh \
    build-essential \
    libpq-dev \
    wget \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Create odoo user
RUN useradd -m -d /home/odoo -U -r -s /bin/bash odoo

# Set up SSH for GitHub
RUN mkdir -p /home/odoo/.ssh && \
    chown odoo:odoo /home/odoo/.ssh && \
    chmod 700 /home/odoo/.ssh

# Set up git config for user odoo
USER odoo
RUN git config --global user.name "odoo" && \
    git config --global user.email "odoo@example.com"

# Switch back to root to install Python dependencies
USER root

# Copy requirements.txt if you have one, or install Odoo dependencies directly
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set workdir
WORKDIR /home/odoo

# Expose Odoo port
EXPOSE 8069

# Default command (can be overridden by docker-compose)
CMD ["bash"]

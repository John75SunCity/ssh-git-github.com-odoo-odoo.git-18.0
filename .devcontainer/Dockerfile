FROM python:2.7-slim

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
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    libpq-dev \
    wget \
    node-less \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Create odoo user
RUN useradd -m -d /home/odoo -U -r -s /bin/bash odoo

# Update odoo user to John75SunCity
RUN usermod -l John75SunCity -d /home/John75SunCity -m odoo && \
    groupmod -n John75SunCity odoo

# Set up SSH for GitHub
RUN mkdir -p /home/John75SunCity/.ssh && \
    chown John75SunCity:John75SunCity /home/John75SunCity/.ssh && \
    chmod 700 /home/John75SunCity/.ssh

# Set up git config for user John75SunCity
USER John75SunCity
RUN git config --global user.name "John75SunCity" && \
    git config --global user.email "invoices@suncityboxes.com"

# Switch back to root to install Python dependencies
USER root

# Copy requirements.txt if you have one, or install Odoo dependencies directly
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Remove dpkg lock if it exists
RUN rm -f /var/lib/dpkg/lock

# Set workdir
WORKDIR /home/odoo

# Expose Odoo port
EXPOSE 8069

# Default command (can be overridden by docker-compose)
CMD ["bash"]

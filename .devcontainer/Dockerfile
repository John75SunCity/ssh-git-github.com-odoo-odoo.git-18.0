FROM python:3.10-slim

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

# Set up SSH for GitHub
RUN mkdir -p /home/odoo/.ssh && \
    chown odoo:odoo /home/odoo/.ssh && \
    chmod 700 /home/odoo/.ssh

# (Optional) Add your public key for GitHub access
# COPY id_rsa.pub /home/odoo/.ssh/authorized_keys

# Set up git config for user John75SunCity
USER odoo
RUN git config --global user.name "John75SunCity" && \
    git config --global user.email "invoices@suncityboxes.com"

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

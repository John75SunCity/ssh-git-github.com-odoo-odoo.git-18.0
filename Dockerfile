FROM python:2.7-slim

# Update sources.list to use https
RUN sed -i -e 's|http://|https://|g' /etc/apt/sources.list && \
    apt-get update

# Install system dependencies
RUN apt-get install -y \
    git \
    wget \
    node-less \
    npm \
    python-dev \
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    libjpeg-dev \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set workdir
WORKDIR /odoo

# Expose default Odoo port
EXPOSE 8069

# Default command (override as needed)
CMD ["bash"]

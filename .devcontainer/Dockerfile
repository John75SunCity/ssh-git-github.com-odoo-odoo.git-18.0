# Use official Python 3.10 base for Odoo 18 compatibility
FROM python:3.10-slim-bookworm

# Set environment variables for Python efficiency
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies (combined for layer efficiency)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    fontconfig \
    git \
    libbz2-dev \
    libevent-dev \
    libffi-dev \
    libfreetype6 \
    libgeoip-dev \
    libjpeg-dev \
    libjpeg62-turbo \
    liblcms2-dev \
    libldap2-dev \
    libopenblas-dev \
    libpng16-16 \
    libpq-dev \
    libreadline-dev \
    libsasl2-dev \
    libsqlite3-dev \
    libssl-dev \
    libwebp-dev \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxml2-dev \
    libxrender1 \
    libxslt1-dev \
    libyaml-dev \
    nodejs \
    npm \
    python3-dev \
    tk-dev \
    uuid-dev \
    wget \
    xfonts-75dpi \
    xfonts-base \
    xz-utils \
    zlib1g-dev \
    zstd \
    && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf for Odoo PDF reports (e.g., bale labels)
RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.debian12_amd64.deb \
    && dpkg -i wkhtmltox_0.12.6.1-3.debian12_amd64.deb \
    && apt-get install -f -y \
    && rm wkhtmltox_0.12.6.1-3.debian12_amd64.deb

# Install rtlcss for Odoo theme support
RUN npm install -g rtlcss

# Create odoo user with home directory
RUN useradd -m -d /home/odoo -U -r -s /bin/bash odoo

# Install Python dependencies (wheel first for better builds)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir wheel setuptools-rust \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Install npm dependencies if package.json exists
COPY package*.json /tmp/
RUN cd /tmp \
    && npm ci \
    && mkdir -p /opt/odoo/node_modules \
    && cp -r node_modules/* /opt/odoo/node_modules/ \
    && rm -rf /tmp/node_modules /tmp/package*

# Set permissions for workspace
RUN mkdir -p /workspace && chown -R odoo:odoo /workspace /home/odoo /opt/odoo

# Set working directory
WORKDIR /workspace

# Switch to odoo user for runtime security
USER odoo

# Expose Odoo ports
EXPOSE 8069 8071 8072

# Default command for interactive dev in Codespaces
CMD ["bash"]

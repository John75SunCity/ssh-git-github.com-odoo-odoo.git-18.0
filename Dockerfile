FROM odoo:8.0

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    python-dev \
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy custom addons
COPY ./custom_addons /mnt/extra-addons

# Set default command
CMD ["odoo"]

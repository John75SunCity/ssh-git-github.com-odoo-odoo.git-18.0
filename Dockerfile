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
    libz-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone Odoo 8.0 source code
RUN git clone --depth 1 --branch 8.0 https://github.com/odoo/odoo.git /odoo

# Install Odoo dependencies
RUN pip install --no-cache-dir -r /odoo/requirements.txt

# Install Odoo from source
RUN cd /odoo && python setup.py install

# Set workdir
WORKDIR /odoo

# Expose default Odoo port
EXPOSE 8069

# Default command (override as needed)
CMD ["bash"]

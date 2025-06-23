# Odoo 8.0 Dockerfile (Python 2.7)
FROM python:2.7-slim

# Set the working directory
WORKDIR /app

# Copy your application files into the container
COPY . /app

# Copy the entire addons directory into the container
COPY addons /mnt/extra-addons

# Ensure the Odoo server uses the correct addons path
ENV ODOO_ADDONS_PATH="/mnt/extra-addons"

# Install any required Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask==1.1.2 requests==2.25.1

# Install Odoo dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    git \
    make \
    gawk \
    bison \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libtiff5-dev \
    libwebp-dev \
    libopenjp2-7-dev \
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
    libpq-dev \
    wget \
    libc6 \
    libc6-dev \
    build-essential \
    manpages-dev \
    perl \
    && rm -rf /var/lib/apt/lists/*

# Clone the Odoo source code
RUN git clone --depth=1 --branch=8.0 https://github.com/odoo/odoo.git /opt/odoo

# Install Python dependencies for Odoo
RUN pip install -r /opt/odoo/requirements.txt

# Add Odoo to PATH
ENV PATH="/opt/odoo:${PATH}"

# Set the default command to run your application
CMD ["python", "/opt/odoo/openerp-server", "--addons-path=/mnt/extra-addons,/opt/odoo/addons"]

# Odoo 8.0 Dockerfile
FROM python:2.7-slim

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        build-essential \
        python-dev \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev \
        libsasl2-dev \
        libldap2-dev \
        libssl-dev \
        libjpeg-dev \
        libpq-dev \
        node-less \
        npm \
        wget \
        gdebi \
        ca-certificates \
        fonts-dejavu-core \
        fonts-dejavu-extra \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    psycopg2==2.7.7 \
    babel==1.3 \
    passlib==1.6.2 \
    werkzeug==0.9.4 \
    decorator==3.4.0 \
    python-dateutil==2.2 \
    pytz==2014.10 \
    six==1.8.0 \
    lxml==3.4.1 \
    mako==1.0.1 \
    jinja2==2.7.3 \
    PyPDF2==1.26.0 \
    pyparsing==2.0.1 \
    reportlab==3.1.44 \
    requests==2.6.0 \
    docutils==0.12 \
    feedparser==5.1.3 \
    gevent==1.0.2 \
    greenlet==0.4.5 \
    html2text==2014.4.5 \
    psutil==2.2.0 \
    psycogreen==1.0 \
    pydot==1.0.2 \
    pyldap==2.4.28 \
    vobject==0.6.6 \
    xlwt==0.7.5 \
    xlrd==0.9.3 \
    xlutils==1.7.1 \
    num2words==0.5.4 \
    passlib==1.6.2 \
    pillow==2.6.1

# Clone Odoo 8.0 from official repo
RUN git clone --depth 1 --branch 8.0 https://www.github.com/odoo/odoo /odoo

# Set working directory
WORKDIR /odoo

# Add entrypoint script
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose Odoo port
EXPOSE 8069

# Default command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["openerp-server"]

'version': '1',

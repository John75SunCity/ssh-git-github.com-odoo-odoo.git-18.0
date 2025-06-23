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

# Set the default command to run your application
CMD ["python", "your_script.py"]

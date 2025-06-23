# Odoo 8.0 Dockerfile (Python 2.7)
FROM python:2.7-slim

# Set the working directory
WORKDIR /app

# Copy your application files into the container
COPY . /app

# Install any required Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask==1.1.2 requests==2.25.1

# Set the default command to run your application
CMD ["python", "your_script.py"]

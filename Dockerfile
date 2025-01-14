# Base image with Python 3.10
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY src/ ./src
COPY datasets/ ./datasets
COPY requirements.txt ./
COPY application.py ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8080

# Expose port (if necessary)
EXPOSE 8080

# Command to run the application
CMD ["python", "application.py"]

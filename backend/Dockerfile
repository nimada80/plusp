# Dockerfile for Django backend (admin_panel + console)
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements (if exists) and install first for caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -i https://pypi.org/simple -r requirements.txt

# Copy project files
COPY . .

# Collect static files (if needed)
# RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8010

# Run migrations and start server
ENTRYPOINT ["/app/entrypoint.sh"]

FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install dependencies
RUN apt-get update \
    && apt-get -y install netcat-openbsd libpq-dev gcc \
    && pip install --upgrade pip \
    && pip install psycopg2



# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project code into the container
COPY . /app/

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["sh", "/app/entrypoint.sh"]

# Command to run the Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

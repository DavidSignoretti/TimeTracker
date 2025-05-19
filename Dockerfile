# Use a Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app

# Install the Python dependencies using pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the application code into the container
COPY . /app

# Expose the port that your Flask app will run on (default is 5000)
EXPOSE 5000

# Command to run the Flask application using gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]

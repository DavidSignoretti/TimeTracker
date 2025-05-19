To run your Flask app using Docker, you'll need to create a Dockerfile and then use Docker to build and run your application. Here's a step-by-step guide:
1. Prerequisites:
* Docker installed on your system.


2. Project Setup:
* Create a directory for your Flask project.
* Place your Flask application file (e.g., `app.py`) in this directory.
* If you have any dependencies, create a `requirements.txt` file:

* ```bash
    uv pip freeze > requirements.txt
    ```

* Create a `Dockerfile` in the same directory.


3. Dockerfile:
* The `Dockerfile` contains instructions for building a Docker image for your Flask application. Here's a common example:

    ```dockerfile
    # Use a Python base image (you can choose a specific version)
    FROM python:3.11-slim

    # Set the working directory inside the container
    WORKDIR /app

    # Copy the requirements file into the container
    COPY requirements.txt /app

    # Install the Python dependencies using pip or uv
    RUN pip install --no-cache-dir -r /app/requirements.txt
    #Or if you want to use uv
    #RUN pip install uv && uv pip install --no-cache-dir -r /app/requirements.txt

    # Copy the application code into the container
    COPY . /app

    # Expose the port that your Flask app will run on (default is 5000)
    EXPOSE 5000

    # Command to run the Flask application.  Use gunicorn for production.
    CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
    # If your Flask app is in a file named "app.py" and the Flask
    # application instance is named "app".  Adjust as needed.
    ```


4. Build the Docker Image:
* Open a terminal or command prompt.
* Navigate to the directory containing your `Dockerfile`.
* Build the Docker image:

    ```bash
    docker build -t my-flask-app .
    ```

    * `docker build`:  The command to build a Docker image.
    * `-t my-flask-app`:  Tags the image with the name "my-flask-app".  Choose a meaningful name.
    * `.`:  Specifies the current directory as the build context (where the Dockerfile and application code are located).


5. Run the Docker Container:
* Run the Docker container based on the image you just built:

    ```bash
    docker run -p 5000:5000 my-flask-app
    ```

    * `docker run`:  The command to run a container.
    * `-p 5000:5000`:  Maps port 5000 on your host machine to port 5000 inside the container.  This allows you to access the Flask app from your browser.
    * `my-flask-app`:  The name of the image to run.


6. Access the Application:
* Open your web browser and go to `http://localhost:5000/`.  You should see your Flask application running.


Explanation:
Dockerfile: A blueprint for creating a Docker image. It specifies the base image, dependencies, application code, and the command to run.
Image: A lightweight, standalone, executable package that includes everything needed to run an application (code, runtime, system tools, system libraries, settings).
Container: A running instance of a Docker image.
Using Docker Compose (Optional, for more complex apps):
If your application has multiple services (e.g., a database), you can use Docker Compose to define and manage them.
Create a docker-compose.yml file:
version: '3.8'
services:
  timetracker:
    build: .  # Build from the current directory
    ports:
      - "5000:5000"
    volumes:
      - sqlite_data:/app/instance  # Maps the SQLite database directory to a named volume
    restart: unless-stopped
    environment:
      - FLASK_APP=main.py
      - FLASK_ENV=production

volumes:
  sqlite_data:  # This creates a named volume that persists the SQLite database


Run the application with Docker Compose:
docker-compose up -d  # -d runs in detached mode (in the background)

The docker-compose.yml file above includes a named volume (sqlite_data) that maps to the /app/instance directory where the SQLite database is stored. This ensures that your database data persists across container restarts and even removals.

When the container restarts (either manually or due to the "restart: unless-stopped" policy), it will automatically reconnect to the same SQLite database stored in the volume. This happens because:
1. Docker volumes exist independently of containers and persist data between container lifecycles
2. When a container starts, Docker automatically mounts the configured volumes
3. The Flask application is configured to look for the database in the instance folder
4. SQLAlchemy's "pool_pre_ping" option helps ensure database connections are reestablished after interruptions

To stop the application:
docker-compose down  # This stops the containers but preserves the volumes

To completely remove everything including the database volume:
docker-compose down -v  # The -v flag removes the volumes

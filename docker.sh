# Build the image
docker build -t xstrat-qu-tracker .

docker-compose down -v

# Run the container using the command from docker.txt
docker run -d --name xstrat-qu-tracker \
-p 5001:5001 \
-v sqlite_data:/app/instance \
-e FLASK_APP=main.py \
-e FLASK_ENV=production \
--restart unless-stopped \
xstrat-qu-tracker

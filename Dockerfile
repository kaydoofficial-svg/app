FROM python:3.11-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY index.html .
COPY login.html .

# Serve index.html via Flask too
RUN pip install --no-cache-dir flask

EXPOSE 5050

CMD ["python", "server.py"]

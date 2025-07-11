FROM python:3.13-slim
WORKDIR /app

# Install curl + Docker CLI
RUN apt-get update && apt-get install -y curl \
    && curl -fsSL https://get.docker.com | sh \
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# RUN mkdir -p /app/logs
# Ensure log directory exists with write permissions
RUN mkdir -p /app/logs && chmod 777 /app/logs

ENTRYPOINT ["python"]
CMD ["server.py"]

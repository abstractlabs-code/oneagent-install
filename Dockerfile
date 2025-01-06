FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY install_oneagent.py /app/
COPY requirements.txt /app/


RUN apt-get update && \
    apt-get install -y --no-install-recommends unzip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


CMD ["python3", "install_oneagent.py"]

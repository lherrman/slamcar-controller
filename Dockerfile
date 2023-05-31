
# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt

# Install required libraries
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxrender1 libxext6 libgl1 && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install -r requirements.txt
COPY . .
EXPOSE 5001 5002

CMD ["python", "main.py"]

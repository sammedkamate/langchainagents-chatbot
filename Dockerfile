FROM python:3.11.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents-docker.py .

RUN mkdir -p responses

CMD ["python", "agents-docker.py"]
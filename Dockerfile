# backend/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code
RUN apt-get update && apt-get install -y libreoffice && apt-get clean
RUN apt-get update && apt-get install -y libmagic1 libmagic-dev

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
COPY ./wait-for-db.py /wait-for-db.py

# (Optional) Ensure it's executable
RUN chmod +x /wait-for-db.py

EXPOSE 5000
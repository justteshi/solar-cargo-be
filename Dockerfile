# backend/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .
COPY ./wait-for-db.py /wait-for-db.py

# (Optional) Ensure it's executable
RUN chmod +x /wait-for-db.py

EXPOSE 5000
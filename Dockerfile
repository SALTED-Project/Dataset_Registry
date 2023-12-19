# syntax=docker/dockerfile:1
FROM python:3.10-alpine

RUN apk add --no-cache git

WORKDIR /app
COPY src /app 
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "dataset_registry_module.py"]

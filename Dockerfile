FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt /app/
RUN pip --no-cache-dir install -r requirements.txt
COPY app.py /app/
ENTRYPOINT ["python3", "app.py"]

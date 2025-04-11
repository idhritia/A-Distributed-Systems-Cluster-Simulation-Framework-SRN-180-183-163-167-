FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
COPY static/ ./static/
COPY templates/ ./templates/
CMD ["python", "app.py"]
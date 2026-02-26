FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create necessary directories
RUN mkdir -p data logs output

ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--mode", "full", "--emails", "20"]

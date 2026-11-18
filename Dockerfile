FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

# keep container awake-friendly: discord gateway auto-reconnects
CMD ["python", "-u", "bot.py"]

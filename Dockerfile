FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home ragb && mkdir /app/data && chown ragb /app/data
COPY bot.py .
COPY ragb ./ragb
USER ragb
ENV PYTHONUNBUFFERED=1
CMD ["python", "bot.py"]

FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ app/
COPY seed_resumes/ seed_resumes/
COPY calendars/ calendars/
COPY jds/ jds/
EXPOSE 8000
# Single worker: SQLite ATS requires one writer. Scale reads, not writers,
# or migrate ATS to Postgres before adding workers.
CMD ["sh", "-c", "uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

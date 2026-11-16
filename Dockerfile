# 1. Start from a small official Python image
FROM python:3.12-slim

# 2. Do not write .pyc files; show logs immediately
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3. All commands below run inside /app
WORKDIR /app

# 4. Copy only requirements first, so Docker can cache the installed packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the project
COPY . .

# 6. Run as a normal user, not root (safer)
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

# 7. The app listens on this port (Render sets PORT automatically)
ENV PORT=8000
EXPOSE 8000

# 8. Start the production server
CMD gunicorn run:app --bind 0.0.0.0:${PORT} --workers 2

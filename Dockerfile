FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Static assets do not require production secrets or a live database at build time.
RUN SECRET_KEY=build-only DB_ENGINE=sqlite python manage.py collectstatic --noinput

USER app

CMD ["gunicorn", "--config", "gunicorn.conf.py", "rovoca.wsgi:application"]

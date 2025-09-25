FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE 'config.settings'

WORKDIR /app

RUN apt-get update && apt-get install -y     libpq-dev     gcc     python3-dev     netcat-openbsd

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
COPY ././entrypoint.sh app/entrypoint.sh
RUN chmod +x  app/entrypoint.sh
COPY . .

#RUN #chmod +x  entrypoint.sh
#EXPOSE 8000
ENTRYPOINT ["app/entrypoint.sh"]
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:8000"]

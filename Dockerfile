FROM python:3.14.6-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings_railway
WORKDIR /app

COPY requirements.txt requirements-railway.txt ./
RUN python -m pip install --no-cache-dir -r requirements-railway.txt

COPY manage.py gunicorn.conf.py ./
COPY config/ config/
COPY chamados/ chamados/
COPY equipamentos/ equipamentos/
COPY templates/ templates/
COPY static/ static/
COPY assets/ assets/
COPY iniciar-hospedagem.sh ./

CMD ["sh", "iniciar-hospedagem.sh"]

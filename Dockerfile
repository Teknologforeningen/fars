FROM python:3-slim as build
EXPOSE 8888
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
RUN apt update && apt install -y gcc git libpq-dev libsasl2-dev python-dev libldap2-dev libssl-dev
COPY requirements.txt .
RUN pip install gunicorn && pip install -r requirements.txt
COPY fars .
RUN python manage.py migrate
CMD exec gunicorn --timeout 90 --bind 0.0.0.0:8888 fars.wsgi:application
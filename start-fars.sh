#!/bin/bash
# start-fars.sh
echo $MIGRATE

if [ "$MIGRATE" == "True" ]; then
	echo "Performing migration"
	python fars/manage.py migrate
fi
python fars/manage.py collectstatic -v0 --noinput
touch fars/fars/wsgi.py
cd fars
gunicorn fars.wsgi:application --bind 0.0.0.0:8010 --workers 3
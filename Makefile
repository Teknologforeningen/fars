install: bin/python

bin/python:
	virtualenv -p /usr/bin/python3 .
	bin/pip install -r requirements.txt

migrate: bin/python
	bin/python fars/manage.py migrate

serve: bin/python
	bin/python fars/manage.py runserver 8000

deploy: bin/python
	bin/python fars/manage.py collectstatic -v0 --noinput
	touch fars/fars/wsgi.py

clean:
	rm -rf bin/ lib/ build/ dist/ *.egg-info/ include/ local/

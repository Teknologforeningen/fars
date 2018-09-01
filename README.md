# fars
Reservation system with modifiable bookables and timeslots
Make sure that you have Python 3 installed and virtualenv to go with it.

## Dev environment setup

`cd` into the `fars` directory and do the following:

1. Create virtualenv: `virtualenv -p /usr/bin/python3 venv`
2. Activate venv: `source venv/bin/activate`
3. Install stuff with pip: `pip install -r requirements.txt`
4. Run migrations: `python fars/manage.py migrate`

Now you can run the dev instance: `python fars/manage.py runserver`
View the page in your browser: `http://localhost:8000`

# Fantastiskt Användbara ReservationsSystemet FARS [![Build Status](https://travis-ci.org/Teknologforeningen/fars.svg?branch=master)](https://travis-ci.org/Teknologforeningen/fars)

Reservation system with modifiable bookables and timeslots.
Make sure that you have Python 3 and pip installed and virtualenv to go with it.

## Development environment setup

Install prerequisites
```
sudo apt install virtualenv python3 python3-pip libsasl2-dev python3-dev libldap2-dev libssl-dev
```

`cd` into the `fars` directory and do the following:

Create virtualenv
```
virtualenv -p /usr/bin/python3 venv
```
Activate venv\
```
source venv/bin/activate
```
Install prerequisites with pip
```
pip install -r requirements.txt
```
Run migrations
```
python fars/manage.py migrate
```

Now you can run the dev instance
```
python fars/manage.py runserver
```
View the page in your browser: ```http://localhost:8000```

## Base setup

Create a superuser account
```
python manage.py createsuperuser
```
Use this account to log in on the adminsite
```
http://localhost:8000/admin
```
This adminpanel is where you will do all top-level administrating such as creating bookables, adding users (if you don't have another database for that) and choosing which users are admins over which bookables. This is about all setup you need to start using the system.

## Permissions of different usertypes

### Administrators

The top-level admins are able to access the admin site where they manage bookables, bookablespecific admins and other users. They are also able to remove any booking from any bookable as well as making bookings that don't follow the restrictions of the bookable, e.g. very long bookings and bookings that are far in the future. Bookablespecific admins have the same powers over bookings but only regarding the bookable they are admins for.

### Authenticated users

Logged in users can view the different bookables in the system and make bookings for them. They can also unbook their own bookings.

### Non-authenticated users

Users that haven't logged into the site can only view the bookables that are public. All other functionality requires them to log in.

### Metadata forms

If your bookable requires any kind of metadata to be attached to each booking, simply create a standard django form in `fars/booking/metadata_forms.py`, then add it to the `METADATA_FORM_OPTIONS` and `METADATA_FORM_CLASSES` dicts. The data will be stored in the booking's `metadata` field.

## Built with

* [Django](https://www.djangoproject.com/) - The web framework used
* [FullCalendar](https://fullcalendar.io/) - Javascript plugin used for the calendar

## Authors
* Thomas Langenskiöld
* Castor Köhler

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

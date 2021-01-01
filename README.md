# Infer Backend

Infer Backend is a backend server stack using Django REST Framework.

## Dependencies Installation
	
	$ pip install django==2.2
	$ pip install djangorestframework
	$ pip install django-cors-headers==3.5.0
	$ python3 manage.py runserver

## Usage

	cd into root cc-be directory
	$ python3 manage.py runserver
	// Run once then migrate to initialize the datebase
	$ python3 manage.py migrate
	$ python3 manage.py runserver
	To authenticate, POST to /auth/ then put the token in the header as such {'Authorization': 'Token <token>'}
	To create a admin account, use the command: python3 manage.py createsuperuser

## Available Command

	BROWSER	/admin/

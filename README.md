# infer-backend

infer-backend is a backend server stack for the senior project using Django REST Framework.

## Dependencies Installation
	
	$ pip3 install django
	$ pip3 install djangorestframework
	$ pip3 install django-cors-headers

## Usage

	cd into root directory
	$ python3 manage.py runserver
	// Run once then migrate to init the db
	$ python3 manage.py migrate
	$ python3 manage.py runserver
	To authenticate, POST to /auth/ then put the token in the header as such {'Authorization': 'Token <token>'}
	To create a admin account, use the command: python3 manage.py createsuperuser

## Available Command

	BROWSER	/admin/
	POST	/auth/
	GET		/api/user/
	POST	/api/user/		(username,password,first_name,last_name,email)
	GET		/api/user/<username>/
	GET	/api/user/<username>/courts/
	GET		/api/project/
	POST	/api/project/	(name,description)
	GET		/api/project/<project_name>/
	POST	/api/project/<project_name>/add_user/		(user)
	POST	/api/project/<project_name>/remove_user/	(user)
	

	


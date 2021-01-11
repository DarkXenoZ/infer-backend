# infer-backend

infer-backend is a backend server stack for the project using Django REST Framework.

## Dependencies Installation
	
	$ pip install django==3.1
	$ pip install djangorestframework
	$ pip install django-cors-headers==3.6.0
	$ python3 manage.py runserver

## Usage

	cd into root directory
	$ python3 manage.py runserver
	// Run once then migrate to initialize the datebase
	$ python3 manage.py migrate
	$ python3 manage.py runserver
	To authenticate, POST to /auth/ then put the token in the header as such {'Authorization': 'Token <token>'}
	To create a admin account, use the command: python3 manage.py createsuperuser

## Available Command

	BROWSER	/admin/
	POST	/auth/
	GET	/api/log/
	GET	/api/user/
	POST	/api/user/		(username,password,first_name,last_name,email)
	GET	/api/user/<username>/
	GET	/api/user/<username>/project/
	POST	/api/user/<username>/change_password	(password)
	GET	/api/project/
	POST	/api/project/	(name,description)
	GET	/api/project/<project_id>/
	POST	/api/project/<project_id>/add_user/		(username)
	POST	/api/project/<project_id>/remove_user/	(username)
	POST	/api/project/<project_id>/add_dicom/		(id)
	POST	/api/project/<project_id>/remove_dicom/	(id)
	POST	/api/project/<project_id>/edit_dicom/	(dicom_id,diag_id)
	GET	/api/project/<project_id>/list_dicom/
	GET	/api/pipeline/
	GET	/api/pipeline/<pipeline_id>
	POST	/api/pipeline/	(name,id)
	GET	/api/dicom/
	GET	/api/dicom/<dicom_id>
	POST	/api/dicom/		(name,data)
	GET	/api/diag/
	GET	/api/diag/<diag_id>
	POST	/api/diag/		(name)

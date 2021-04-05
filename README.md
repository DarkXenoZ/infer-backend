# infer-backend

infer-backend is a backend server stack for the project using Django REST Framework.

## Dependencies Installation

	$ pip install -r requirements.txt
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
	DELETE	/api/user/<username>/
	PUT	/api/user/<username>/		(first_name | last_name | email)
	PUT	/api/user/<username>/update_batch		(users, (first_name | last_name | email))
	GET	/api/user/<username>/project/
	PUT	/api/user/<username>/change_password	(password)
	GET	/api/project/	
	POST	/api/project/	(name,description,task,cover,predclasses) predclasses ex : covid,normal
	GET	/api/project/<project_id>/
	PUT	/api/project/<project_id>/		(name | task | cover | description | predclasses)
	DELETE	/api/project/<project_id>/
	POST	/api/project/<project_id>/add_user/		(username)
	POST	/api/project/<project_id>/add_user_batch/		(users) users ex : user1,user2,user3	
	GET	/api/project/<project_id>/list_pipeline/	(id)
	POST	/api/project/<project_id>/add_pipeline/	(name,pipeline_id,description,operator)
	POST	/api/project/<project_id>/upload_dicom/		(dicom)
	POST	/api/project/<project_id>/upload_image/		(image,patient_name,patient_id,physician_name,patient_age,content_date:YMD)
	POST	/api/project/<project_id>/infer_image/	(image_ids:list,pipeline:id	)
	GET	/api/project/<project_id>/list_uninfer_image/	(pipeline:id)
	GET	/api/project/<project_id>/list_image/
	GET	/api/pipeline/
	GET	/api/pipeline/<pipeline_id>
	PUT	/api/pipeline/<pipeline_id>		(name | pipeline_id | operator | accuracy | description)
	DELETE	/api/pipeline/<pipeline_id>
	GET	/api/image/
	GET	/api/image/<image_id>
	PUT	/api/image/<image_id>/verify_image/	(actual_class,note)
	DELETE	/api/image/<image_id>/
	GET	/api/predictResult/
	GET	/api/predictResult/<predictResult_id>

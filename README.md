# CC-BE

CC-BE is a backend server stack for the courtcatch project using Django REST Framework.

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
	GET	/api/user/
	POST	/api/user/
	GET	/api/user/<username>/
	GET	/api/user/<username>/courts/
	POST	/api/user/<username>/change_password/
	POST	/api/user/<username>/add_credit/
	POST	/api/booking/<id>/cancel/
	GET	/api/booking/<id>/get_rackets/
	GET	/api/booking/<id>/get_shuttlecocks/
	POST	/api/booking/<id>/reserve_racket/
	POST	/api/booking/<id>/buy_shuttlecock/
	GET	/api/log/
	GET	/api/log/<username>/
	GET	/api/court?name=<name>&rating=<min_rating>&dist=<max_dist>&lat=<lat>&long=<long>&sort_by=<name|-name|dist|rating>
	GET /api/court?rackets_count=<count>&end_time=<end>&start_time=<start>&day_of_the_week=<day_of_the_week>
	GET /api/court?shuttlecocks_count=<count>
	POST	/api/court/
	GET	/api/court/<courtname>/
	POST	/api/court/<courtname>/rate_court/
	POST	/api/court/<courtname>/add_image/
	POST	/api/court/<courtname>/book/
	POST	/api/court/<courtname>/add_racket/
	POST	/api/court/<courtname>/add_shuttlecock/
	POST	/api/court/<courtname>/topup_shuttlecock/
	POST	/api/shuttlecock/<bookId>/cancel/
	POST	/api/racket/<bookId>/cancel/
	GET	/api/document/
	POST	/api/document/
	GET	/api/document/<username>/
	POST	/auth/


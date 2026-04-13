dev:
	powershell -ExecutionPolicy Bypass -Command "$$env:ENV_FILE='.env.local'; python manage.py runserver"

staging:
	powershell -ExecutionPolicy Bypass -Command "$$env:ENV_FILE='.env.staging'; python manage.py runserver"

migrate-dev:
	powershell -ExecutionPolicy Bypass -Command "$$env:ENV_FILE='.env.local'; python manage.py migrate"

migrate-staging:
	powershell -ExecutionPolicy Bypass -Command "$$env:ENV_FILE='.env.staging'; python manage.py migrate"

superuser-dev:
	powershell -ExecutionPolicy Bypass -Command "$$env:ENV_FILE='.env.local'; python manage.py createsuperuser"

superuser-staging:
	powershell -ExecutionPolicy Bypass -Command "$$env:ENV_FILE='.env.staging'; python manage.py createsuperuser"

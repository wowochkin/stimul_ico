VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

.PHONY: init install run migrate superuser collectstatic docker-build docker-up docker-down

init:
	python3.11 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install:
	$(PIP) install -r requirements.txt

migrate:
	$(PY) backend/manage.py migrate

superuser:
	$(PY) backend/manage.py createsuperuser

run:
	$(PY) backend/manage.py runserver 0.0.0.0:8000

collectstatic:
	$(PY) backend/manage.py collectstatic --noinput

docker-build:
	docker build -t stimul-ico:latest .

docker-up:
	docker run --rm --name stimul-ico \
		-p 8000:8000 \
		--env-file .env \
		-v $(PWD)/docker_data/db.sqlite3:/app/backend/db.sqlite3 \
		-v $(PWD)/docker_data/staticfiles:/app/staticfiles \
		stimul-ico:latest

docker-down:
	docker stop stimul-ico || true


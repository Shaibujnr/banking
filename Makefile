install:
	pip install --upgrade pip
	pip install poetry
	poetry install

test:
	pytest --cov=banking tests/
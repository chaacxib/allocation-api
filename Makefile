## Install for production
install:
	poetry install --without dev

## Install for development 
install-dev:
	poetry install --with dev

## Run tests
test:
	pytest --tb=short

## Watch tests
watch-tests:
	ls *.py | entr pytest --tb=short

## Run checks (isort, black, mypy, ruff)
check:
	isort .
	black .
	pyright .
	ruff .

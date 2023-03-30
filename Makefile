# these will speed up builds, for docker-compose >= 1.25
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

## Install for production
install:
	poetry install --without dev

## Install for development 
install-dev:
	poetry install --with dev

## Run tests
test:
	pytest tests/ --tb=short

## Watch tests
watch-tests:
	ls *.py | entr pytest --tb=short

## Run checks (isort, black, pyright, ruff)
check:
	isort src/ tests/
	black src/ tests/
	pyright --stats src/ tests/
	ruff src/ tests/

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs app | tail -100
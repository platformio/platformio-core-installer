lint:
	pylint --rcfile=./.pylintrc ./pioinstaller ./scripts ./templates

isort:
	isort -rc ./pioinstaller
	isort -rc ./tests
	isort -rc ./scripts
	isort -rc ./templates

format:
	black --target-version py27 ./pioinstaller
	black --target-version py27 ./tests
	black --target-version py27 ./scripts
	black --target-version py27 ./templates

test:
	py.test --log-cli-level=INFO --verbose --capture=no --exitfirst -n 6 --dist=loadscope tests

before-commit: isort format lint pack test

clean:
	find . -name \*.pyc -delete
	find . -name __pycache__ -delete
	rm -rf .cache
	rm -rf build
	rm -rf htmlcov
	rm -f .coverage

profile:
	# Usage $ > make PIOARGS="boards" profile
	python -m cProfile -o .tox/.tmp/cprofile.prof $(shell which platformio) ${PIOARGS}
	snakeviz .tox/.tmp/cprofile.prof

publish:
	python setup.py sdist upload

pack:
	python scripts/pack.py
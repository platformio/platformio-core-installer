lint:
	pylint --rcfile=./.pylintrc ./pioinstaller

isort:
	isort -rc ./pioinstaller
	isort -rc ./tests

format:
	black --target-version py27 ./pioinstaller
	black --target-version py27 ./tests

test:
	py.test --verbose --capture=no --exitfirst tests

pack:
	pioinstaller pack

before-commit: isort format lint

clean:
	find . -name \*.pyc -delete
	find . -name __pycache__ -delete
	rm -rf .cache

publish:
	python setup.py sdist upload
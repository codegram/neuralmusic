deps:
	conda env update --prefix ./env --file conda.yml && source activate ./env

lint:
	source activate ./env && flake8 *.py src tests

test:
	source activate ./env && pytest tests

test-ci:
	mkdir -p test-reports && source activate ./env && pytest --junitxml=test-reports/junit.xml

clean:
	rm -fr logs mlruns test-reports outputs model.pkl

.PHONY: deps lint test clean

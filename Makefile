data:
	spell run --machine-type CPU --conda-file=conda.yml --mount uploads/midi:midi 'python data.py data.etl.tar_gz_path=/spell/neuralmusic/midi/midi.tar.gz data.etl.outdir=/spell/neuralmusic/out; rm -fr outputs'

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

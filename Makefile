SRC = $(wildcard nbs/*.ipynb)

all: build docs

dev:
	jupyter notebook

build: $(SRC)
	nbdev_build_lib
	touch neuralmusic

docs_serve: docs
	cd docs && bundle exec jekyll serve

docs: $(SRC)
	PYTHONPATH=nbs nbdev_build_docs
	touch docs

test:
	PYTHONPATH=nbs nbdev_test_nbs --flags test

data:
	spell run --machine-type CPU --conda-file=conda.yml --mount uploads/midi:midi 'SPELL=True python data.py data.etl.tar_gz_path=/spell/neuralmusic/midi/midi.tar.gz data.etl.outdir=/spell/neuralmusic/out; rm -fr outputs'

deps:
	conda env update --prefix ./env --file conda.yml && source activate ./env
	cd docs && bundle install

.PHONY: deps
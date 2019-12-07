SRC = $(wildcard nbs/*.ipynb)

all: build docs

build: $(SRC)
	nbdev_build_lib
	touch neuralmusic

docs_serve: docs
	cd docs && bundle exec jekyll serve

docs: $(SRC)
	nbdev_build_docs
	touch docs

test:
	nbdev_test_nbs --flags test

data:
	spell run --machine-type CPU --conda-file=conda.yml --mount uploads/midi:midi 'SPELL=True python data.py data.etl.tar_gz_path=/spell/neuralmusic/midi/midi.tar.gz data.etl.outdir=/spell/neuralmusic/out; rm -fr outputs'

deps:
	conda env update --prefix ./env --file conda.yml && source activate ./env && pip install nbdev
	cd docs && bundle install

.PHONY: deps
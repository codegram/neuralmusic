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

lint:
	flake8 neuralmusic

test:
	PYTHONPATH=nbs nbdev_test_nbs --flags test

etl:
	spell run --machine-type CPU --conda-file=conda.yml --mount uploads/tv-midi-621:midi 'SPELL=True PYTHONPATH=. bin/etl data.etl.midi_path=/spell/neuralmusic/midi data.etl.outdir=/spell/neuralmusic/out; rm -fr outputs'

deps:
	conda env update --prefix ./env --file conda.yml && activate ./env
	pip install spell nb_black nbdev jupyter
	cd docs && bundle install

.PHONY: deps

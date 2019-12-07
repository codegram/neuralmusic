import math
import os
import time
import logging
from pathlib import Path
from typing import Collection

import hydra
import prefect
import fastparquet
import spell.metrics
from prefect import task, Flow
from prefect.engine.executors import DaskExecutor
from prefect.engine.signals import SKIP
from prefect.tasks.shell import ShellTask

from neuralmusic.midi import parse_midi_file

log = logging.getLogger("data")

total_songs = 0
malformed_songs = 0
valid_songs = 0
valid_notes = 0

started_at = None

if "SPELL" in os.environ:
    metric = spell.metrics.send_metric

    def metric(_logger, k, v):
        spell.metrics.send_metric(k, v)


else:

    def metric(logger, k, v):
        logger.info(f"[{k}]: {v}")


def report(logger):
    elapsed = time.time() - started_at
    metric(logger, "Total Songs", total_songs)
    metric(logger, "Malformed Songs", malformed_songs)
    metric(logger, "Notes", valid_notes)
    metric(logger, "Total Songs / second", (total_songs / elapsed))
    metric(logger, "Notes / second", (valid_notes / elapsed))


@task
def untar_cmd(file_path: str, outdir: str) -> str:
    """
    Untars a .tar.gz file onto a directory (will create it if it does not exist).
    """
    if os.path.exists(outdir):
        raise SKIP("Output directory already exists.")
    return f"mkdir -p {outdir} && tar -zxf {file_path} -C {outdir}"


@task(skip_on_upstream_skip=False)
def partition_files(
    data_path: str, partition_size: int = 100, min_partitions: int = 4
) -> list:
    """
    Partitions the midi files in data_path into chunks.
    """
    midi_files = list(Path(data_path).glob("**/*.mid"))
    n = len(midi_files)
    if (n / partition_size) < min_partitions:
        partition_size = math.ceil(n / min_partitions)
    logger = prefect.context.get("logger")
    logger.info(
        f"Processing {n} MIDI files partitioned into groups of {partition_size}"
    )
    return [
        midi_files[i : i + partition_size]
        for i in range(0, len(midi_files), partition_size)
    ]


@task
def process_and_write(mini_batch: Collection[str], outdir: str) -> bytes:
    """
    Parses a mini batch of MIDI files and writes the results to a parquet file.
    The filename is determined by `map_index`. Returns the amount of notes it parsed.
    """
    frame_no = prefect.context.get("map_index")
    Path(outdir).mkdir(parents=True, exist_ok=True)
    outfile = f"{outdir}/out_{frame_no}.parq"

    logger = prefect.context.get("logger")

    should_append = False

    global total_songs
    global valid_songs
    global valid_notes
    global malformed_songs

    for file in mini_batch:
        df, processed_notes = parse_midi_file(file)
        if df is not None:
            valid_songs += 1
            valid_notes += processed_notes

            fastparquet.write(outfile, df, compression="SNAPPY", append=should_append)
            del df
            should_append = True
        else:
            malformed_songs += 1
            logger.warning(f"[Minibatch {frame_no}] {file} could not be processed.")

        total_songs += 1
        report(logger)

    return outfile


@task
def combine_parquet_files(files: Collection[str]) -> None:
    """
    Combines N parquet files with the same schema into another one.
    """
    fastparquet.writer.merge(files)


untar = ShellTask(name="untar_task")


def etl(cfg):
    """
    Builds the ETL flow.
    """
    tar_gz_path = cfg.tar_gz_path
    outdir = cfg.outdir
    assert tar_gz_path, "Config not found: data.etl.tar_gz_path"
    assert outdir, "Config not found: data.etl.outdir"

    with Flow("Neuralmusic data ETL") as flow:
        tar_gz_path = Path(cfg.tar_gz_path).resolve()
        assert tar_gz_path.exists(), f"{tar_gz_path} does not exist"
        command = untar_cmd(str(tar_gz_path), "data")
        untarred = untar(command=command)

        mini_batches = partition_files(
            "data", partition_size=cfg.partition_size, upstream_tasks=[untarred]
        )

        partitions = process_and_write.map(mini_batches, outdir=outdir)

        combine_parquet_files(partitions)

    return flow


@hydra.main(config_path="config/config.yaml", strict=False)
def main(cfg):
    flow = etl(cfg.data.etl)
    if cfg.data.etl.dry_run:
        log.info("Dry run -- visualizing flow only")
        flow.visualize()
    else:
        log.info("Executing flow")
        executor = DaskExecutor(
            n_workers=cfg.data.etl.num_workers,
            threads_per_worker=cfg.data.etl.threads_per_worker,
        )
        global started_at
        started_at = time.time()
        flow.run(executor=executor)


if __name__ == "__main__":
    main()

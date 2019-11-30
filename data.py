import math
import os
import logging
from pathlib import Path
from typing import Collection

import hydra
import prefect
import fastparquet
import pandas as pd
from dask.distributed import Client
from prefect import task, Flow
from prefect.engine.signals import SKIP
from prefect.engine.executors import DaskExecutor
from prefect.tasks.shell import ShellTask

from src.midi import parse_midi_file

log = logging.getLogger("data")


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
    notes = 0

    logger = prefect.context.get("logger")

    n = 0
    valid_n = 0
    total = len(mini_batch)
    df = pd.DataFrame()
    for file in mini_batch:
        n += 1
        new_df, processed_notes = parse_midi_file(file)
        if new_df is not None:
            df = pd.concat([df, new_df])
        notes += processed_notes
        if processed_notes != 0:
            valid_n += 1
            logger.info(
                f"[Minibatch {frame_no}] {notes} notes in {valid_n}/{total} songs"
            )
        else:
            logger.warning(f"[Minibatch {frame_no}] {file} could not be processed.")

    fastparquet.write(outfile, df, compression="SNAPPY")
    logger.info(f"[Minibatch {frame_no}] COMPLETE! Wrote {notes} notes to {outfile}")

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
        client = Client(
            n_workers=cfg.data.etl.num_workers,
            threads_per_worker=cfg.data.etl.threads_per_worker,
        )
        executor = DaskExecutor(address=client.scheduler.address)
        flow.run(executor=executor)


if __name__ == "__main__":
    main()

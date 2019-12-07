import logging

import hydra
from prefect.engine.executors import DaskExecutor

from neuralmusic.data.etl import build_etl, init_stats

log = logging.getLogger("etl")


@hydra.main(config_path="config/config.yaml", strict=False)
def main(cfg):
    flow = build_etl(cfg.data.etl)
    if cfg.data.etl.dry_run:
        log.info("Dry run -- visualizing flow only")
        flow.visualize()
    else:
        log.info("Executing flow")
        executor = DaskExecutor(
            n_workers=cfg.data.etl.num_workers,
            threads_per_worker=cfg.data.etl.threads_per_worker,
        )
        init_stats()
        flow.run(executor=executor)


if __name__ == "__main__":
    main()

FROM nvidia/cuda:10.2-runtime

RUN mkdir -p /workspace

VOLUME /workspace

RUN apt-get update && apt-get install curl git-core build-essential -y
RUN curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh > /miniconda.sh
RUN bash /miniconda.sh -b -p /miniconda

RUN touch /root/.bashrc && \
    echo 'export LC_ALL=C.UTF-8' >> /root/.bashrc && \
    echo 'export LANG=C.UTF-8' >> /root/.bashrc && \
    echo 'export PYTHONPATH=/workspace/project' >> /root/.bashrc && \
    echo 'export PATH="/miniconda/bin:$PATH"' >> /root/.bashrc && \
    echo 'source /miniconda/bin/activate' >> /root/.bashrc
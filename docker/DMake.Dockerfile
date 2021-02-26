# Image to build shift-4-haystack
# See the accompanying LICENSE file.
# (C) 2021 Engie Digital
#
# build-arg:
# UID: uid to use (use --build-arg UID=$(id -u) before mapping the source directory)
# AWS_PROFILE: profile to use (`default` by default)
# AWS_REGION: AWS region (`eu-west-3` by default)
#
# To use the project directory, map /shaystack (-v $PWD:/shaystack )
# To use docker inside this container, use :
# docker run \
#   --group-add $(getent group docker | cut -d: -f3) \
#   -v /var/run/docker.sock:/var/run/docker.sock \
#   ...

FROM continuumio/miniconda3
MAINTAINER Philippe PRADOS

ARG PRJ=shaystack
# Use host user id to be capable to use -v $(PWD):/shaystack
ARG USERNAME=${PRJ}
# May be mapped to the host user id ( --build-arg UID=$(id -u) )
ARG UID=1000
ARG VENV=docker-${PRJ}
ARG AWS_PROFILE=default
ARG AWS_REGION=eu-west-3
ARG PYTHON_VERSION=3.7
ARG USE_OKTA=N
ARG PIP_INDEX_URL=https://pypi.python.org/pypi
ARG PIP_EXTRA_INDEX_URL=
ARG PORT=3000

RUN apt-get update ; \
    apt-get install -y make nano vim docker.io ; \
    apt-get clean ; \
    rm -rf /var/lib/apt/lists/*
RUN adduser --disabled-password --uid ${UID} --gecos '' ${USERNAME} && \
    chmod -R go+rw /opt/conda

RUN mkdir /${PRJ} && \
    chown ${UID}:${UID} /${PRJ} && \
    printf "#!/usr/bin/env bash\nsource $(conda info --base)/etc/profile.d/conda.sh\nconda activate $VENV\n\${@}\n" >/bin/conda_run ; \
    chmod 755 /bin/conda_run

USER ${USERNAME}
SHELL ["/bin/bash", "-c"]
ENV VENV=${VENV} \
    PYTHON_VERSION=${PYTHON_VERSION} \
    PIP_INDEX_URL=${PIP_INDEX_URL} \
    PIP_EXTRA_INDEX_URL=${PIP_EXTRA_INDEX_URL} \
    USE_OKTA=${USE_OKTA} \
    AWS_PROFILE=${AWS_PROFILE} \
    AWS_REGION=${AWS_REGION}
RUN mkdir -p ~/.aws && \
    printf "[default]\nregion = ${AWS_REGION}\n" > ~/.aws/config && \
    printf "\n[${AWS_PROFILE}]\nregion = ${AWS_REGION}\n\n" >> ~/.aws/config && \
    printf "[${AWS_PROFILE}]\n" >> ~/.aws/credentials
RUN conda init bash && \
    echo "conda activate ${VENV}" >> ~/.bashrc

# May be mapped to current host projet directory ( -v $PWD:/$PRJ )
USER root
COPY . /${PRJ}
RUN chown -R ${UID}:${UID} /${PRJ}
USER ${USERNAME}

WORKDIR /${PRJ}
RUN make configure
EXPOSE ${PORT}

ENTRYPOINT ["/bin/conda_run","make"]
CMD ["help"]

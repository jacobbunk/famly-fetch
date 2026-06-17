# Runner image for scripts/ci-local.sh.
#
# `act` runs the workflow inside catthehacker/ubuntu:act-latest, but that image
# no longer ships a `node` binary on PATH. actions/checkout and
# actions/setup-python are JavaScript actions whose main and post steps run via
# `node`, so without it the job fails with:
#   exec: "node": executable file not found in $PATH  (exit 127)
#
# This image extends the same base and installs Node.js 24 so those actions and
# their post steps run cleanly. scripts/ci-local.sh builds it automatically.
FROM catthehacker/ubuntu:act-latest

ARG NODE_MAJOR=24

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
        | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_${NODE_MAJOR}.x nodistro main" \
        > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && node --version

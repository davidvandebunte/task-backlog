#!/usr/bin/env bash
JUPYTER_LAB_PORT="$1"
WORKING_DIR="$2"

DOCKER_TAG="personal-backlog-jupyter-lab"
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
docker build --tag "$DOCKER_TAG" - < "$SCRIPTPATH"/Dockerfile

# Start a jupyter lab server
# https://jupyter-docker-stacks.readthedocs.io/en/latest/using/common.html
# https://github.com/jupyter/docker-stacks/blob/2d9aa71f69f7a623b073769b43998ba0078246ce/base-notebook/start.sh
# https://jupyterhub.readthedocs.io/en/stable/getting-started/config-basics.html
docker run --rm \
    -p "$JUPYTER_LAB_PORT":"$JUPYTER_LAB_PORT" \
    --env JUPYTER_ENABLE_LAB=yes \
    --env NB_USER="$USER" \
    --volume "$HOME":"$HOME" \
    --user root \
    --workdir "$HOME" \
    "$DOCKER_TAG" \
    start.sh jupyter lab \
    --port "$JUPYTER_LAB_PORT" \
    --notebook-dir="$WORKING_DIR" \
    --NotebookApp.password='sha1:5970cc8206fe:82124bd5879c43de97768e910e3e13d2534d5a63'

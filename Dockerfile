# https://hub.docker.com/r/jupyter/scipy-notebook/tags/
FROM "jupyter/scipy-notebook:0c84b71d9f3d"

# Better to install with conda?
RUN pip install \
  uncertainties==3.1.1 \
  pint==0.9

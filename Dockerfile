# https://hub.docker.com/r/jupyter/scipy-notebook/tags/
FROM "jupyter/scipy-notebook:0c84b71d9f3d"

# Better to install with conda?
RUN conda install \
  uncertainties==3.1.1 \
  jira=2.0.0 \
  pint==0.9

# Build docker image with sample plugin `myplugin`.

# From the root directory of the repository (where this Dockerfile is), build an image named "restraint_test" with
#     docker build -t brer_restraint .
# Note that public images for dockerhub are build with `docker build -t gmxapi/brer_restraint:tag .`
#
# Launch an ephemeral container with
#     docker run --rm -ti -p 8888:8888 brer_restraint
# for the Jupyter notebook server, or, for just a shell
#     docker run --rm -ti brer_restraint bash
# The container will be removed when the process (notebook server or shell) exits.
# To create and run a named container, do something like the following.
#     docker run -ti --name restraint_test brer_restraint
#
# Test with
#     docker run --cpus 2 --rm -ti brer_restraint bash -c \
#         "cd /home/jovyan/brer_restraint/tests && mpiexec -n 2 python -m mpi4py -m pytest"
# or replace `gmxapi/brer_restraint:devel` with your local image name


# The base image is available on DockerHub, but you can also build your own from the gmxapi repository.
FROM gmxapi/gmxapi:0.0.7

# Hot fix: clean out accidental cruft from an upstream base image.
RUN rm -rf /home/jovyan/sample_restraint /home/jovyan/plugin-build

# Grab some additional useful biomolecular simulation analysis tools.
RUN conda config --add channels conda-forge
RUN conda install mdanalysis

# This is a bit risky and troublesome, but I want to test the current repo state without committing.
# Another problem is that changes to directories do not trigger build cache invalidation!
COPY --chown=1000 CMakeLists.* README.md /home/jovyan/brer_restraint/
COPY --chown=1000 cmake/ /home/jovyan/brer_restraint/cmake/
COPY --chown=1000 docs/ /home/jovyan/brer_restraint/docs/
COPY --chown=1000 external/ /home/jovyan/brer_restraint/external/
COPY --chown=1000 src/ /home/jovyan/brer_restraint/src/
COPY --chown=1000 external/ /home/jovyan/brer_restraint/external/
COPY --chown=1000 tests/ /home/jovyan/brer_restraint/tests/

COPY --chown=1000 examples/example.ipynb /home/jovyan/brer_restraint/examples/
COPY --chown=1000 examples/job.sh /home/jovyan/brer_restraint/examples/
COPY --chown=1000 examples/restrained-ensemble.py /home/jovyan/brer_restraint/examples/
COPY --chown=1000 examples/strip_notebook.py /home/jovyan/brer_restraint/examples/

# Prune the directory after removed or find will try to descend into a nonexistant directory
RUN find /home/jovyan -name __pycache__ -exec rm -rf \{\} \; -prune

# Build and install the plugin in the Conda virtual environment from the scipy-jupyter base image.
RUN mkdir /home/jovyan/plugin-build && \
    (cd /home/jovyan/plugin-build && \
    GROMACS_DIR=/home/jovyan/install/gromacs gmxapi_DIR=/home/jovyan/install/gromacs \
        cmake ../brer_restraint \
            -DPYTHON_EXECUTABLE=/opt/conda/bin/python && \
    LD_LIBRARY_PATH=/opt/conda/lib make && \
    GROMACS_DIR=/home/jovyan/install/gromacs make test && \
    make install)

RUN GROMACS_DIR=/home/jovyan/install/gromacs \
    PYTHONPATH=plugin-build/src/pythonmodule \
    CONDA_DIR=/opt/conda \
        /opt/conda/bin/python -m pytest brer_restraint/tests --verbose

RUN GROMACS_DIR=/home/jovyan/install/gromacs \
    PYTHONPATH=plugin-build/src/pythonmodule \
    CONDA_DIR=/opt/conda \
        mpiexec -n 2 /opt/conda/bin/python -m mpi4py -m pytest brer_restraint/tests --verbose


# The jupyter notebook server might not pick this up, but we can make it a little easier to find the
# `gmx` binary from the default user shell.
RUN echo "source install/gromacs/bin/GMXRC.bash" >> /home/jovyan/.profile

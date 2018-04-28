# Build docker image with sample plugin `myplugin`

FROM gmxapi/gmxapi:0.0.5

# Allow build for an arbitrary branch or tag, but default to the tip of `master`
ARG BRANCH=master

RUN wget https://github.com/eirrgang/sample_restraint/archive/$BRANCH.zip

RUN unzip $BRANCH.zip

RUN mv sample_restraint-$BRANCH /home/jovyan/samplerestraint

RUN mkdir -p /home/jovyan/plugin-build && \
    (cd /home/jovyan/plugin-build && \
    GROMACS_DIR=/home/jovyan/install/gromacs gmxapi_DIR=/home/jovyan/install/gromacs cmake ../samplerestraint -DPYTHON_EXECUTABLE=`which python` && \
    LD_LIBRARY_PATH=/opt/conda/lib make && \
    make test) && \
    PYTHONPATH=plugin-build/src/pythonmodule python -m pytest samplerestraint/tests --verbose

# Test with
# docker run --rm -ti samplerestraint bash -c "cd /home/jovyan/samplerestraint/tests && PYTHONPATH=/home/jovyan/plugin-build/src/pythonmodule/ mpiexec -n 2 python -m mpi4py -m pytest"

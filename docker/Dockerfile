# This Dockerfile is used to produce a working installation of gmxpy and libgmxapi
# against which to develop plugins. The sample plugin is also built, but not installed.
# These dependencies are currently in private repositories, so they should be
# retrieved before building the docker image so that the sources are available in
# the same directory as the Dockerfile as 'gromacs-gmxapi' and 'gmxpy'.
#
# This is the second of two Dockerfiles that separate the GROMACS build from the build of the
# gmx python module. Use Dockerfile.gmxapi first to produce the 'gmxapi' docker image.
#
#     # Get this repository and this Dockerfile
#     mkdir docker-build-dir
#     cd docker-build-dir
#     git clone git@bitbucket.org:kassonlab/samplerestraint.git
#     cp samplerestraint/Dockerfile ./
#
#     # Get the dependencies
#     git clone git@bitbucket.org:kassonlab/gromacs_api.git gromacs-gmxapi
#     (cd gromacs-gmxapi && git checkout develop-0.0.3)
#     git clone git@bitbucket.org:kassonlab/gmxpy-dev.git gmxpy
#
#     # Build the image with this Dockerfile
#     docker build 

FROM gmxapi

WORKDIR /external

ADD gmxpy /external/gmxpy
ADD samplerestraint /external/samplerestraint

ADD scripts /external/scripts

RUN pip3 install --upgrade setuptools && \
    pip install --upgrade setuptools

RUN pip3 install --upgrade cmake && \
    pip install --upgrade cmake

RUN pip3 install --upgrade pytest && \
    pip install --upgrade pytest && \
    pip3 install --upgrade tox && \
    pip install --upgrade tox

RUN bash -x /external/scripts/setuptoolsinstall.sh

# To be able to step through with gdb, run with something like the following, replacing
# 'imagename' with the name of the docker image built with this recipe.
# docker run --rm -ti --security-opt seccomp=unconfined imagename bash
CMD bash -x /external/scripts/buildplugin.sh




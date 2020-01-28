# Copyright (c) 2020 Microsoft
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

FROM mcr.microsoft.com/azureml/base:intelmpi2018.3-ubuntu16.04
ENV STAN_VERSION 2.21.0
ENV CPLUS_INCLUDE_PATH=/opt/miniconda/include:/opt/miniconda/include/python3.7m
ENV STAN_PATH=/usr/local/cmdstan-${STAN_VERSION}

RUN mkdir ${STAN_PATH} && \
    wget https://github.com/stan-dev/cmdstan/releases/download/v${STAN_VERSION}/cmdstan-${STAN_VERSION}.tar.gz -P /tmp && \
    tar xvfz /tmp/cmdstan-${STAN_VERSION}.tar.gz --directory /usr/local/ && \
    cd ${STAN_PATH} && \
    # Change settings for STAN installation with IntelMPI
    echo "using mpi : mpicxx :" > ${STAN_PATH}/stan/lib/stan_math/lib/boost_1.69.0/user-config.jam && \
    echo "<include>/opt/intel/compilers_and_libraries_2018.3.222/linux/mpi/intel64/include " >> ${STAN_PATH}/stan/lib/stan_math/lib/boost_1.69.0/user-config.jam && \
    echo "<library-path>/opt/intel/compilers_and_libraries_2018.3.222/linux/mpi/intel64/lib/release_mt " >> ${STAN_PATH}/stan/lib/stan_math/lib/boost_1.69.0/user-config.jam && \
    echo "<library-path>/opt/intel/compilers_and_libraries_2018.3.222/linux/mpi/intel64/lib " >> ${STAN_PATH}/stan/lib/stan_math/lib/boost_1.69.0/user-config.jam && \
    echo "<find-shared-library>mpicxx" >> ${STAN_PATH}/stan/lib/stan_math/lib/boost_1.69.0/user-config.jam && \
    echo "<find-shared-library>mpifort " >> ${STAN_PATH}/stan/lib/stan_math/lib/boost_1.69.0/user-config.jam && \
    echo "<find-shared-library>mpi " >> ${STAN_PATH}/stan/lib/stan_math/lib/boost_1.69.0/user-config.jam && \
    echo "<find-shared-library>mpigi " >> ${STAN_PATH}/stan/lib/stan_math/lib/boost_1.69.0/user-config.jam && \
    echo "<find-shared-library>dl " >> ${STAN_PATH}/stan/lib/stan_math/lib/boost_1.69.0/user-config.jam && \
    echo "<find-shared-library>rt " >> ${STAN_PATH}/stan/lib/stan_math/lib/boost_1.69.0/user-config.jam && \
    echo "<find-shared-library>pthread ;" >> ${STAN_PATH}/stan/lib/stan_math/lib/boost_1.69.0/user-config.jam && \
    # Set general STAN settings
    echo "STAN_MPI=true" >> ${STAN_PATH}/make/local && \
    echo "CXX=mpicxx" >> ${STAN_PATH}/make/local && \
    echo "TBB_CXX_TYPE=gcc" >> ${STAN_PATH}/make/local && \
    # Make STAN
    make build -j $(nproc) && \
    # Remove the downloaded file to reduce the overall size
    rm /tmp/cmdstan-${STAN_VERSION}.tar.gz

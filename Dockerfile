FROM continuumio/miniconda3:4.9.2 as conda

# create base environment, installing things that are better packaged in conda right away
RUN conda create -p /opt/env -c conda-forge python=3.8 notebook matplotlib-base sncosmo iminuit

RUN . /opt/conda/etc/profile.d/conda.sh && \
    conda activate /opt/env && \
    pip install ampel-ztf

ADD . /src/ampel-contrib-sample

RUN . /opt/conda/etc/profile.d/conda.sh && \
    conda activate /opt/env && \
    pip install --no-deps \
    /src/ampel-contrib-sample \
    'ampel-ipython @ https://github.com/AmpelProject/Ampel-ipython/archive/master.tar.gz'

# Use C.UTF-8 locale to avoid issues with ASCII encoding
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

ENV XDG_CACHE_HOME=/opt/env/share/cache
ENV XDG_CONFIG_HOME=/opt/env/etc
ENV JUPYTER_CONFIG_DIR=/opt/env/etc/jupyter
ENV JUPYTER_DATA_DIR=/opt/env/share/cache/jupyter
ENV JUPYTER_RUNTIME_DIR=/opt/env/share/cache/jupyter/runtime

# Have Jupyter notebooks launch without additional command line options
RUN . /opt/conda/etc/profile.d/conda.sh && \
    conda activate /opt/env && \
    jupyter notebook --generate-config && \
    sed -i -e "/allow_root/ a c.NotebookApp.allow_root = True" ${JUPYTER_CONFIG_DIR}/jupyter_notebook_config.py && \
    sed -i -e "/custom_display_url/ a c.NotebookApp.custom_display_url = \'http://localhost:8891\'" ${JUPYTER_CONFIG_DIR}/jupyter_notebook_config.py && \
    sed -i -e "/c.NotebookApp.ip/ a c.NotebookApp.ip = '0.0.0.0'" ${JUPYTER_CONFIG_DIR}/jupyter_notebook_config.py && \
    sed -i -e "/c.NotebookApp.token/ a c.NotebookApp.token = ''" ${JUPYTER_CONFIG_DIR}/jupyter_notebook_config.py && \
    sed -i -e "/c.NotebookApp.password/ a c.NotebookApp.password = ''" ${JUPYTER_CONFIG_DIR}/jupyter_notebook_config.py && \
    sed -i -e "/open_browser/ a c.NotebookApp.open_browser = False" ${JUPYTER_CONFIG_DIR}/jupyter_notebook_config.py

# Make cache dirs
RUN for lib in astropy matplotlib jupyter; do \
      for base in ${XDG_CACHE_HOME} ${XDG_CONFIG_HOME}; do \
        mkdir -p ${base}/${lib}; \
      done; \
    done

# Ensure that config builds, and create matplotlib/astropy caches
RUN /opt/env/bin/ampel-config build > /opt/env/etc/ampel_config.yml || \
    /opt/env/bin/ampel-config build -v

# Repoint mongo URI
RUN sed -i -e "s|mongodb://localhost:27017|mongodb://mongo:27017|g" /opt/env/etc/ampel_config.yml

# Make cache dir writable
RUN chmod -R og+rwx ${XDG_CACHE_HOME} && \
    chmod -R og+rwx ${XDG_CONFIG_HOME}

# Copy to primary container
FROM gcr.io/distroless/base-debian10

ENV PATH=/opt/env/bin
ENV OMP_NUM_THREADS=1
ENV XDG_CACHE_HOME=/opt/env/share/cache
ENV XDG_CONFIG_HOME=/opt/env/etc
ENV JUPYTER_CONFIG_DIR=/opt/env/etc/jupyter
ENV JUPYTER_DATA_DIR=/opt/env/share/cache/jupyter
ENV JUPYTER_RUNTIME_DIR=/opt/env/share/cache/jupyter/runtime
ENV AMPEL_CONFIG=/opt/env/etc/ampel_config.yml

USER nobody

COPY --from=conda /opt/env /opt/env

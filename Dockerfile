# Stage 1: Build Environment
FROM fedora:41

# Install necessary packages
RUN dnf update -y && \
    dnf install -y python3 python3-pip python3-gobject gtk4 xauth mesa-libGL mesa-dri-drivers which python3-pipenv
RUN dnf clean all -y

# Set user and group IDs
ARG USER_ID=1000
ARG GROUP_ID=1000
ARG USER_NAME=jiracreator
RUN groupadd -g ${GROUP_ID} ${USER_NAME} && \
    useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash ${USER_NAME}

# Set working directory
WORKDIR /app

# Change ownership of directories
RUN chown -R ${USER_NAME}:${USER_NAME} /app
COPY * /app/

# Create necessary directories and set permissions
RUN mkdir -vp /run/user/${USER_ID}/at-spi /home/${USER_NAME}/.cache /home/${USER_NAME}/.config
RUN chown -R ${USER_NAME}:${USER_NAME} /app /run/user/${USER_ID} /home/${USER_NAME}/.cache /home/${USER_NAME}/.config

# Switch to the created user
USER ${USER_NAME}

# Set environment variables
ENV XDG_RUNTIME_DIR=/run/user/${USER_ID}
ENV LIBGL_ALWAYS_SOFTWARE=1

# Install Python dependencies
RUN pipenv install --dev

USER 0

RUN ln -s /home/jiracreator/.local/bin/py.test /usr/bin/pytest

# Switch to the created user
USER ${USER_NAME}

# Copy application code
COPY . /app

# Set display environment variable
ENV DISPLAY=:0
ENV GTK_THEME=Adwaita:dark

# Set Python path
ENV PYTHONPATH="/usr/lib/python3/dist-packages:${PYTHONPATH}"

# Mount host's GTK theme configuration directory into the container
VOLUME /usr/share/themes
VOLUME /tmp/.X11-unix

# Set entrypoint command
WORKDIR /app/jira_creator
CMD ["python3", "rh_jira.py"]
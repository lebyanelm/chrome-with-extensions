# PULL BASE IMAGE
FROM selenium/standalone-chrome:latest


# Install unzip if needed for extension handling
USER root
RUN apt-get update && apt-get install -y python3-pip ffmpeg
USER seluser


# SETUP ENVIRONMENT VARIABLES
ENV WORK_DIR=/home/seluser/token-manager
ENV LOG_LEVEL=debug
ENV DISPLAY=:99
ENV CHROME_DRIVER_VERSION=latest
ENV DISABLE_DEV_SHM=true
ENV SE_NODE_OVERRIDE_MAX_SESSIONS=true


# COPY THE CODE AND INSTALL DEPENDENCIES
RUN mkdir /home/seluser/token-manager
COPY ./ /home/seluser/token-manager
RUN pip install -r /home/seluser/token-manager/requirements.txt


# Initialise running of the scripts
CMD ["python3", "/home/seluser/__manager__.py"]
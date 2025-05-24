FROM selenium/standalone-chrome:latest

USER root

RUN apt-get update && apt-get install -y python3-pip ffmpeg

ENV WORK_DIR=/home/seluser/token-manager
ENV LOG_LEVEL=debug
ENV DISPLAY=:99
ENV CHROME_DRIVER_VERSION=latest
ENV DISABLE_DEV_SHM=true
ENV SE_NODE_OVERRIDE_MAX_SESSIONS=true

RUN mkdir -p $WORK_DIR
COPY ./ $WORK_DIR
RUN pip install -r $WORK_DIR/requirements.txt

RUN chown -R seluser:seluser $WORK_DIR

USER seluser
ENTRYPOINT ["/home/seluser/token-manager/entrypoint.sh"]
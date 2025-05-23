FROM selenium/standalone-chrome:latest

# Install unzip if needed for extension handling
USER root
RUN apt-get update && apt-get install -y unzip
USER seluser

ENV DISPLAY=:99
ENV CHROME_DRIVER_VERSION=latest
ENV DISABLE_DEV_SHM=true
ENV SE_NODE_OVERRIDE_MAX_SESSIONS=true
ENV SE_NODE_MAX_SESSIONS=1

# Expose Selenium port
EXPOSE 4444

# Copy extensions
RUN mkdir /home/seluser/extensions
COPY ./extensions /home/seluser/extensions

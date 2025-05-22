FROM selenium/standalone-chrome:latest

# Install unzip if needed for extension handling
USER root
RUN apt-get update && apt-get install -y unzip
USER seluser

ENV DISPLAY=:99
ENV CHROME_DRIVER_VERSION=latest
ENV DISABLE_DEV_SHM=true

# Copy extensions
COPY ./extensions /home/seluser/extensions
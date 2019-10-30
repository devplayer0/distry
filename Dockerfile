FROM python:3.8-alpine

COPY requirements.txt /opt/
RUN apk --no-cache add pkgconf libvirt musl-dev gcc libvirt-dev && \
    pip install -r /opt/requirements.txt && \
    apk --no-cache del pkgconf musl-dev gcc libvirt-dev
RUN apk --no-cache add openssh

COPY distry/ /opt/distry
WORKDIR '/opt'
STOPSIGNAL SIGINT
ENTRYPOINT ["python", "-u", "-m", "distry"]

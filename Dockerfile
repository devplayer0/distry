FROM python:3.8-alpine

COPY requirements.txt /opt/
RUN apk --no-cache add openssh libvirt pkgconf musl-dev gcc libvirt-dev && \
    pip install -r /opt/requirements.txt && \
    apk --no-cache del pkgconf musl-dev gcc libvirt-dev

WORKDIR '/opt'
RUN mkdir -p distry/static && \
    wget -O - https://github.com/novnc/noVNC/archive/v1.1.0.tar.gz | tar zx && mv noVNC-* distry/static/novnc
COPY distry/ /opt/distry

STOPSIGNAL SIGINT
ENTRYPOINT ["python", "-u", "-m", "distry"]

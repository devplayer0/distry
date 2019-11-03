FROM python:3.8-alpine

COPY requirements.txt /opt/
RUN echo "@testing http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
RUN apk --no-cache add openresty@testing redis openssh libvirt pkgconf musl-dev gcc libvirt-dev && \
    pip install -r /opt/requirements.txt && \
    apk --no-cache del pkgconf musl-dev gcc libvirt-dev

WORKDIR '/opt'
RUN wget -O - https://github.com/novnc/noVNC/archive/v1.1.0.tar.gz | tar zx && mv noVNC-* novnc
COPY distry/ /opt/distry
RUN mkdir /tmp/nginx && ln -s /tmp/nginx /var/tmp/nginx
COPY redis.conf openresty.conf /opt/

STOPSIGNAL SIGINT
ENTRYPOINT ["python", "-u", "-m", "distry"]

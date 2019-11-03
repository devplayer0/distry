# Distry
_Try a Linux distro without having to download or install anything!_

## What is this?
TL;DR: Spin up a VM on a remote server and access it through your browser. All resources are released once the tab is
closed.

When a user requests for a new VM to be created, Distry picks from a list of configured [libvirt](https://libvirt.org)
hosts and creates a new domain (with configured resource limits). The browser is then redirected to a page with
[noVNC](https://novnc.com/info.html) connected to the VM. A snippet of JavaScript sends a heartbeat request to the
backend every few seconds to prevent the VM from being destroyed for lack of use.

The VNC connection is proxied through nginx over WS(S) (aka websockets) and therefore can be encrypted easily (since
websockets are negotiated over HTTP(s)).

# Deployment
To deploy Distry, you'll need a [Docker](https://docs.docker.com/install/) (probably
[Docker Compose](https://docs.docker.com/compose/install/) too) and a box running libvirt with SSH access.

A very simple [`docker-compose.yaml`](docker-compose.yaml) is provided in this repo. You'll need to create a
`config.yaml` to configure your hypervisor(s) and distros. See the provided [`config.yaml.example`](config.yaml.example)
for available options and their meanings.

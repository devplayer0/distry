import string
import xml.etree.ElementTree as ET
from os import path
import tempfile

import shortuuid
import libvirt
from libvirt import libvirtError

class VirtException(Exception):
    pass

def next_id():
    return shortuuid.uuid()[:10]

with open(path.join(path.dirname(__file__), 'template_volume.xml')) as f:
    VOLUME_TEMPLATE = string.Template(f.read())
with open(path.join(path.dirname(__file__), 'template.xml')) as f:
    DOM_TEMPLATE = string.Template(f.read())

class Hypervisor:
    def __init__(self, distros, hostname, key, max_vms, instance_config, port=22, username='root'):
        self.distros = distros
        self.hostname = hostname
        self.instance_config = instance_config
        if 'dom_prefix' not in self.instance_config:
            self.instance_config['dom_prefix'] = 'distry-'
        if 'storage_pool' not in self.instance_config:
            self.instance_config['storage_pool'] = 'distry'
        if 'network' not in self.instance_config:
            self.instance_config['network'] = 'distry'
        self.max_vms = max_vms
        self.vms = {}

        with tempfile.NamedTemporaryFile('w', prefix='distry', suffix='.key') as keyfile:
            keyfile.write(key)
            keyfile.flush()

            self.conn = libvirt.open((f'qemu+ssh://{username}@{hostname}:{port}/system'
                                      f'?keyfile={keyfile.name}&no_verify=1&sshauth=privkey'))
        self.storage_pool = self.conn.storagePoolLookupByName(self.instance_config['storage_pool'])

    def new_vm(self, distro):
        id_ = next_id()
        dom_name = f'{self.instance_config["dom_prefix"]}{id_}'

        vol = self.storage_pool.createXML(VOLUME_TEMPLATE.substitute(
                name=id_,
                size=self.instance_config['disk']
            ),
            flags=libvirt.VIR_STORAGE_VOL_CREATE_PREALLOC_METADATA)
        try:
            vnc_password = shortuuid.uuid()
            dom = self.conn.defineXMLFlags(DOM_TEMPLATE.substitute(
                    name=dom_name,
                    iso=self.distros[distro],
                    storage_volume=id_,
                    vnc_password=vnc_password,
                    **self.instance_config
                ),
                flags=libvirt.VIR_DOMAIN_DEFINE_VALIDATE)

            try:
                dom.create()
                vnc_port = int(ET.fromstring(dom.XMLDesc()).find('./devices/graphics').attrib['websocket'])
                self.vms[id_] = (dom, vol)
            except:
                dom.undefineFlags(flags=libvirt.VIR_DOMAIN_UNDEFINE_NVRAM)
                raise
        except:
            vol.delete()
            raise

        return id_, vnc_port, vnc_password

    def delete_vm(self, id_):
        dom, vol = self.vms[id_]
        if dom.isActive():
            dom.destroy()

        dom.undefineFlags(flags=libvirt.VIR_DOMAIN_UNDEFINE_NVRAM)
        vol.delete()

    def close(self):
        for id_ in self.vms:
            self.delete_vm(id_)
        self.conn.close()

    def __enter__(self):
        return self
    def __exit__(self, t, v, tb):
        self.close()

class VMManager:
    def __init__(self, config):
        self.config = config
        self.distros = config['distros']
        self.hypervisors = [Hypervisor({k: config['distros'][k]['paths'][hostname] for k in config['distros']}, \
            hostname, **conf) for hostname, conf in config['hypervisors'].items()]
        self.vms = {}

        if not self.hypervisors:
            raise VirtException('at least one hypervisor must be configured')

    def next_hypervisor(self):
        hyp_by_count = {}
        for h in self.hypervisors:
            count = len(list(filter(lambda d: d.startswith(h.instance_config['dom_prefix']),
                h.conn.listDefinedDomains())))
            if count < h.max_vms:
                hyp_by_count[h.hostname] = h
        hyp_by_count = [hyp_by_count[hostname] for hostname in sorted(hyp_by_count, key=hyp_by_count.get)]

        if not hyp_by_count:
            raise VirtException('no capacity available')
        return hyp_by_count[0]

    def new_vm(self, distro):
        hypervisor = self.next_hypervisor()
        id_, *ret = hypervisor.new_vm(distro)
        self.vms[id_] = hypervisor

        return (id_, *ret)
    def delete_vm(self, id_):
        v = self.vms[id_]
        v.delete_vm(id_)
        del self.vms[id_]

    def close(self):
        for h in self.hypervisors:
            h.close()

    def __enter__(self):
        return self
    def __exit__(self, t, v, tb):
        self.close()

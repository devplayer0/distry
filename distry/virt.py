import logging
import xml.etree.ElementTree as ET
from os import path
import tempfile
import time
import threading
import socket

import shortuuid
from flask import render_template
import libvirt
from libvirt import libvirtError
import redis

class VirtException(Exception):
    pass

def next_id():
    return shortuuid.uuid()[:8]

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
        self.redis = redis.Redis(unix_socket_path='/run/redis.sock', decode_responses=True)
        self.lock = threading.RLock()

        with tempfile.NamedTemporaryFile('w', prefix='distry', suffix='.key') as keyfile:
            keyfile.write(key)
            keyfile.flush()

            self.conn = libvirt.open((f'qemu+ssh://{username}@{hostname}:{port}/system'
                                      f'?keyfile={keyfile.name}&no_verify=1&sshauth=privkey'))
        self.storage_pool = self.conn.storagePoolLookupByName(self.instance_config['storage_pool'])

    def new_vm(self, distro):
        with self.lock:
            id_ = next_id()
            dom_name = f'{self.instance_config["dom_prefix"]}{id_}'

            vol = self.storage_pool.createXML(
                render_template('libvirt_volume.xml',
                    name=id_,
                    size=self.instance_config['disk']
                ),
                flags=libvirt.VIR_STORAGE_VOL_CREATE_PREALLOC_METADATA)
            try:
                vnc_password = shortuuid.uuid()
                dom = self.conn.defineXMLFlags(
                    render_template('libvirt_domain.xml',
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
                    self.vms[id_] = {
                        'dom': dom,
                        'vol': vol,
                        'distro': distro,
                        'vnc': {
                            'host': self.hostname,
                            'port': vnc_port,
                            'password': vnc_password
                        }
                    }
                    self.redis.set(id_, f'{socket.gethostbyname(self.hostname)}:{vnc_port}')
                except:
                    dom.undefineFlags(flags=libvirt.VIR_DOMAIN_UNDEFINE_NVRAM)
                    raise
            except:
                vol.delete()
                raise

            return id_

    def delete_vm(self, id_):
        with self.lock:
            info = self.vms[id_]
            dom = info['dom']
            if dom.isActive():
                dom.destroy()

            dom.undefineFlags(flags=libvirt.VIR_DOMAIN_UNDEFINE_NVRAM)
            info['vol'].delete()
            del self.vms[id_]
            self.redis.delete(id_)

    def close(self):
        with self.lock:
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
        id_ = hypervisor.new_vm(distro)
        self.vms[id_] = hypervisor

        return id_
    def get_vm(self, id_):
        return self.vms[id_].vms[id_]
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

class Monitor:
    def __init__(self, manager):
        self.manager = manager
        self.heartbeats = {}
        self.lock = threading.RLock()
        self.running = False

    def refresh(self, id_):
        if id_ not in self.manager.vms:
            raise VirtException(f'vm with id {id_} does not exist')
        with self.lock:
            self.heartbeats[id_] = time.time()

    def run(self):
        while self.running:
            with self.lock:
                defunct = set()
                for id_, last in self.heartbeats.items():
                    if time.time() - last > self.manager.config['heartbeat']['max']:
                        defunct.add(id_)
                for id_ in defunct:
                    try:
                        logging.info('deleting defunct vm %s', id_)
                        self.manager.delete_vm(id_)
                    except Exception as e:
                        logging.error('failed to delete vm %s: %s', id_, e)
                    del self.heartbeats[id_]
            time.sleep(0.5)

    def start(self):
        if self.running:
            raise VirtException('already running')

        self.running = True
        self.thread = threading.Thread(target=self.run)
        self.thread.start()
    def stop(self):
        self.running = False
        self.thread.join()

    def __enter__(self):
        self.start()
        return self
    def __exit__(self, t, v, tb):
        self.stop()

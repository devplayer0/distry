import tempfile

import libvirt

class Hypervisor:
    def __init__(self, hostname, key, instance_size, port=22, username='root'):
        with tempfile.NamedTemporaryFile('w', prefix='distry', suffix='.key') as keyfile:
            keyfile.write(key)
            keyfile.flush()

            self.conn = libvirt.open((f'qemu+ssh://{username}@{hostname}:{port}/system'
                                      f'?keyfile={keyfile.name}&no_verify=1&sshauth=privkey'))

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self
    def __exit__(self, t, v, tb):
        self.close()

class VMManager:
    def __init__(self, config):
        self.hypervisors = [Hypervisor(hostname, **conf) for hostname, conf in config.items()]
        self.current_hypervisor = 0

    def next_hypervisor(self):
        next = self.hypervisors[self.current_hypervisor]

        self.current_hypervisor += 1
        if self.current_hypervisor == len(self.hypervisors):
            self.current_hypervisor = 0

        return next

    def close(self):
        for v in self.hypervisors:
            v.close()

    def __enter__(self):
        return self
    def __exit__(self, t, v, tb):
        self.close()

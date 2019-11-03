import logging
import subprocess

import yaml
from werkzeug.serving import run_simple

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

with open('config.yaml') as conf_file:
    config = yaml.safe_load(conf_file)

redis_proc = subprocess.Popen(['/usr/bin/redis-server', '/opt/redis.conf'])
openresty_proc = subprocess.Popen(['/usr/sbin/nginx', '-c', '/opt/openresty.conf'])

from . import virt
from . import app
app.virt = virt.VMManager(config)
app.virt.monitor = virt.Monitor(app.virt)
app.virt.monitor.start()

try:
    run_simple('unix:///run/distry.sock', 0, app)
finally:
    app.virt.monitor.stop()
    app.virt.close()

    openresty_proc.terminate()
    openresty_proc.wait()

    redis_proc.terminate()
    redis_proc.wait()

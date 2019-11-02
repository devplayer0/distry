import logging

import yaml
from werkzeug.serving import run_simple

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

with open('config.yaml') as conf_file:
    config = yaml.safe_load(conf_file)

from . import virt
from . import app
app.virt = virt.VMManager(config)
app.virt.monitor = virt.Monitor(app.virt)
app.virt.monitor.start()

try:
    run_simple('::', 80, app)
finally:
    app.virt.monitor.stop()
    app.virt.close()

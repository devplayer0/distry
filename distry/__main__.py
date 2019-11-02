import sys

import yaml
from werkzeug.serving import run_simple

with open('config.yaml') as conf_file:
    config = yaml.safe_load(conf_file)

from . import virt
from . import app
app.virt = virt.VMManager(config)

try:
    run_simple('::', 80, app)
finally:
    app.virt.close()

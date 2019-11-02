from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify([d.name() for d in app.virt.next_hypervisor().conn.listAllDomains()])

@app.route('/dom')
def test_volume():
    id_, vnc_port, vnc_pw = app.virt.new_vm('manjaro')
    return jsonify({'id': id_, 'vnc': {'port': vnc_port, 'password': vnc_pw}})

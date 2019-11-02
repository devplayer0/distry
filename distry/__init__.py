from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify([d.name() for d in app.virt.next_hypervisor().conn.listAllDomains()])

@app.route('/vol')
def test_volume():
    return app.virt.new_vm('blah')

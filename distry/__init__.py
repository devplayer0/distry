from flask import Flask, render_template, url_for, redirect, make_response

def js_bool(b):
    return 'true' if b else 'false'

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/newvm')
def new_vm():
    id_, vnc_host, vnc_port, vnc_password = app.virt.new_vm('manjaro')
    res = make_response(redirect(
        url_for('static', filename='novnc/vnc.html',
            autoconnect='true',
            host=vnc_host,
            port=vnc_port,
            path=[''],
            encrypt=js_bool(app.virt.config['novnc']['tls']),
            password=vnc_password),
        code=301))
    res.headers['Cache-Control'] = 'no-cache'
    return res
